<#
.SYNOPSIS
    Calcula MD5 + size + mtime de todos los .xpp bajo SourcePath y vuelca a hashes.csv.

.DESCRIPTION
    Usado por el workflow 02-functional-map para detectar cambios entre sesiones.

    Responsabilidad:
      - Barrido recursivo de .xpp bajo SourcePath.
      - Calcula MD5 del contenido binario (no depende de line-endings ni encoding).
      - Si existe hashes.csv en OutputPath, lo renombra a hashes.previous.csv antes de escribir.
      - Output CSV: file,size,mtime,md5 (con header). Paths normalizados a separador forward slash.

    Determinismo: las filas se ordenan alfabeticamente por 'file' para que el diff entre corridas
    sea estable y las diferencias visuales reflejen cambios reales, no reordenamiento.

    Cross-platform: MD5 sobre contenido binario es deterministico en Windows/Linux/macOS.

.PARAMETER SourcePath
    Carpeta raiz con archivos .xpp (recursivo).

.PARAMETER OutputPath
    Carpeta donde se escribe hashes.csv. Se crea si no existe.

.EXAMPLE
    .\Compute-XppHashes.ps1 -SourcePath '..\XppSource' -OutputPath '..\_tracking'

.NOTES
    Compatibilidad: PowerShell 5.1+ (Windows PowerShell) y PowerShell 7+ (pwsh).
    Encoding de salida: UTF-8 sin BOM.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

# --- Validaciones ---
if (-not (Test-Path -LiteralPath $SourcePath -PathType Container)) {
    throw "SourcePath no existe o no es un directorio: $SourcePath"
}

if (-not (Test-Path -LiteralPath $OutputPath -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

$sourceRoot = (Resolve-Path -LiteralPath $SourcePath).Path
$outputRoot = (Resolve-Path -LiteralPath $OutputPath).Path

$currentCsv  = Join-Path $outputRoot 'hashes.csv'
$previousCsv = Join-Path $outputRoot 'hashes.previous.csv'

# --- Rotacion: hashes.csv existente -> hashes.previous.csv ---
if (Test-Path -LiteralPath $currentCsv) {
    if (Test-Path -LiteralPath $previousCsv) {
        Remove-Item -LiteralPath $previousCsv -Force
    }
    Move-Item -LiteralPath $currentCsv -Destination $previousCsv -Force
    Write-Host "Rotado: hashes.csv -> hashes.previous.csv"
}

# --- Barrido ---
$xppFiles = Get-ChildItem -LiteralPath $sourceRoot -Filter '*.xpp' -Recurse -File -ErrorAction Stop

if ($xppFiles.Count -eq 0) {
    Write-Warning "No se encontraron archivos .xpp bajo $sourceRoot"
}

$rows = @()
$md5  = [System.Security.Cryptography.MD5]::Create()

try {
    foreach ($file in $xppFiles) {
        $absolute = $file.FullName
        $relative = $absolute.Substring($sourceRoot.Length).TrimStart('\', '/') -replace '\\', '/'

        $bytes = [System.IO.File]::ReadAllBytes($absolute)
        $hashBytes = $md5.ComputeHash($bytes)
        $hashHex = ([System.BitConverter]::ToString($hashBytes)).Replace('-', '').ToLowerInvariant()

        $mtimeEpoch = [int64]([DateTimeOffset]$file.LastWriteTimeUtc).ToUnixTimeSeconds()

        $rows += [pscustomobject]@{
            file  = $relative
            size  = $file.Length
            mtime = $mtimeEpoch
            md5   = $hashHex
        }
    }
}
finally {
    $md5.Dispose()
}

# --- Orden deterministico + escritura CSV UTF-8 sin BOM ---
$sortedRows = $rows | Sort-Object -Property file

$header = 'file,size,mtime,md5'
$lines  = @($header)
foreach ($row in $sortedRows) {
    # file no deberia contener comas (paths de X++), pero por las dudas escape basico
    $safeFile = $row.file
    if ($safeFile -match '[,"]') {
        $safeFile = '"' + ($safeFile -replace '"', '""') + '"'
    }
    $lines += "$safeFile,$($row.size),$($row.mtime),$($row.md5)"
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($currentCsv, $lines, $utf8NoBom)

Write-Host "Escritos $($sortedRows.Count) archivos en $currentCsv"
