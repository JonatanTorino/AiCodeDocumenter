<#
.SYNOPSIS
    Parsea archivos .xpp de D365 F&O y produce inventory.csv + dependencies.csv.

.DESCRIPTION
    Cobertura minima v3:
      - class X, class X extends Y, class X implements I1, I2
      - interface IName
      - methods con modificadores (public/private/protected/static/final/abstract/internal)
      - methods en interfaces (sin modificadores)
      - Dependencies: extends, implements, new Z(), X::member

    Limitaciones conocidas:
      - [ExtensionOf(...)] NO se resuelve al parent (la clase aparece, pero sin parent).
      - Macros X++ (#define) y pragmas se ignoran.
      - Tipos de campos y parametros NO se extraen como dependencias (scope futuro).
      - Un solo class/interface por archivo (convencion AxClass).
      - Nombres de clase duplicados entre artefactos (ej: AxnLicParameters existe como AxForm y AxTable)
        producen filas de dependencias ambiguas. El classifier debe desambiguar via columna 'file'.
      - Case-sensitivity en parent: la source puede tener 'common' o 'Common'; se preserva
        el case original. El classifier debe normalizar si necesita agrupar.

.PARAMETER SourcePath
    Carpeta raiz con archivos .xpp (recursivo).

.PARAMETER OutputPath
    Carpeta donde se escriben inventory.csv y dependencies.csv. Se crea si no existe.

.EXAMPLE
    .\Build-XppInventory.ps1 -SourcePath '..\XppSource' -OutputPath '..\_tracking'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$SourcePath,

    [Parameter(Mandatory)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "SourcePath no existe: $SourcePath"
}

if (-not (Test-Path -LiteralPath $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

# Compatibilidad PS 5.1 (sin [Path]::GetRelativePath).
function Get-RelativePath {
    param([string]$Root, [string]$Full)
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $fileFull = [IO.Path]::GetFullPath($Full)
    $sep = [IO.Path]::DirectorySeparatorChar
    if ($fileFull.StartsWith($rootFull + $sep, [StringComparison]::OrdinalIgnoreCase)) {
        return $fileFull.Substring($rootFull.Length + 1)
    }
    return $fileFull
}

# Strings y comentarios generan falsos positivos en los regex de dependencies.
function Remove-XppNoise {
    param([string]$Content)
    $Content = [regex]::Replace($Content, '/\*[\s\S]*?\*/', ' ')
    $Content = [regex]::Replace($Content, '//[^\r\n]*', ' ')
    $Content = [regex]::Replace($Content, '"(?:[^"\\]|\\.)*"', '""')
    $Content = [regex]::Replace($Content, "'(?:[^'\\]|\\.)*'", "''")
    return $Content
}

function Get-XppPrefix {
    param([string]$ClassName)
    $name = $ClassName
    if ($name -match '^I[A-Z]') { $name = $name.Substring(1) }
    if ($name.Length -lt 3) { return $name }
    return $name.Substring(0, 3)
}

function Parse-XppFile {
    param(
        [string]$FilePath,
        [string]$SourceRoot
    )

    $raw = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8
    if (-not $raw) { return $null }
    $clean = Remove-XppNoise -Content $raw

    $modifiers = 'public|private|internal|protected|final|abstract|static|sealed|hookable|replaceable|client|server|display|edit'
    $declPattern = "(?ms)(?:\[[^\]]*\]\s*)?(?:(?:$modifiers)\s+)*(class|interface)\s+([A-Za-z_][A-Za-z_0-9]*)(?:\s+extends\s+([A-Za-z_][A-Za-z_0-9\.]*))?(?:\s+implements\s+([^\{]+?))?\s*\{"
    $declMatch = [regex]::Match($clean, $declPattern)
    if (-not $declMatch.Success) { return $null }

    $kind = $declMatch.Groups[1].Value
    $className = $declMatch.Groups[2].Value
    $parent = $declMatch.Groups[3].Value
    $implementsRaw = $declMatch.Groups[4].Value

    $interfaces = @()
    if ($implementsRaw) {
        $interfaces = $implementsRaw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    }

    $body = $clean.Substring($declMatch.Index + $declMatch.Length)

    # Method count: recorrido linea a linea, contando solo signatures en depth 0 (class-body scope).
    # Evita falsos positivos como "return x(...)" o "throw y(...)" dentro de methods.
    $methodSigPattern = "^\s*(?:(?:$modifiers)\s+)*[A-Za-z_][A-Za-z_0-9\.]*\s+[A-Za-z_][A-Za-z_0-9]*\s*\("
    $depth = 0
    $methodsCount = 0
    foreach ($line in ($body -split "`n")) {
        if ($depth -eq 0 -and $line -match $methodSigPattern) {
            $methodsCount++
        }
        $open = ([regex]::Matches($line, '\{')).Count
        $close = ([regex]::Matches($line, '\}')).Count
        $depth += $open - $close
    }

    $uses = @{}
    foreach ($m in [regex]::Matches($body, '\bnew\s+([A-Za-z_][A-Za-z_0-9\.]*)\s*\(')) {
        $target = $m.Groups[1].Value
        if ($target -ne $className) { $uses[$target] = $true }
    }

    $calls = @{}
    foreach ($m in [regex]::Matches($body, '\b([A-Za-z_][A-Za-z_0-9\.]*)\s*::\s*[A-Za-z_][A-Za-z_0-9]*')) {
        $target = $m.Groups[1].Value
        if ($target -ne $className) { $calls[$target] = $true }
    }

    $relPath = Get-RelativePath -Root $SourceRoot -Full $FilePath

    return [PSCustomObject]@{
        File         = $relPath
        Class        = $className
        Kind         = $kind
        Parent       = $parent
        Interfaces   = ($interfaces -join ';')
        MethodsCount = $methodsCount
        Prefix       = (Get-XppPrefix -ClassName $className)
        Uses         = @($uses.Keys)
        Calls        = @($calls.Keys)
    }
}

# --- Main ---
$files = Get-ChildItem -LiteralPath $SourcePath -Filter '*.xpp' -Recurse -File
Write-Host "Archivos .xpp encontrados: $($files.Count)"

$inventory = New-Object System.Collections.Generic.List[object]
$dependencies = New-Object System.Collections.Generic.List[object]
$skipped = 0

foreach ($file in $files) {
    $parsed = Parse-XppFile -FilePath $file.FullName -SourceRoot $SourcePath
    if (-not $parsed) {
        Write-Warning "Skipped (no class/interface detected): $($file.FullName)"
        $skipped++
        continue
    }

    $inventory.Add([PSCustomObject]@{
        file          = $parsed.File
        class         = $parsed.Class
        parent        = $parsed.Parent
        interfaces    = $parsed.Interfaces
        methods_count = $parsed.MethodsCount
        prefix        = $parsed.Prefix
    })

    if ($parsed.Parent) {
        $dependencies.Add([PSCustomObject]@{
            from_class = $parsed.Class
            to_class   = $parsed.Parent
            kind       = 'extends'
        })
    }

    foreach ($iface in ($parsed.Interfaces -split ';' | Where-Object { $_ })) {
        $dependencies.Add([PSCustomObject]@{
            from_class = $parsed.Class
            to_class   = $iface
            kind       = 'implements'
        })
    }

    foreach ($u in $parsed.Uses) {
        $dependencies.Add([PSCustomObject]@{
            from_class = $parsed.Class
            to_class   = $u
            kind       = 'uses'
        })
    }

    foreach ($c in $parsed.Calls) {
        $dependencies.Add([PSCustomObject]@{
            from_class = $parsed.Class
            to_class   = $c
            kind       = 'calls'
        })
    }
}

$inventoryPath = Join-Path $OutputPath 'inventory.csv'
$dependenciesPath = Join-Path $OutputPath 'dependencies.csv'

$inventory | Export-Csv -Path $inventoryPath -NoTypeInformation -Encoding UTF8
$dependencies | Export-Csv -Path $dependenciesPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "inventory.csv    -> $inventoryPath ($($inventory.Count) filas)"
Write-Host "dependencies.csv -> $dependenciesPath ($($dependencies.Count) filas)"
if ($skipped -gt 0) {
    Write-Host "Skipped          -> $skipped archivos sin class/interface detectada"
}
