# Workflow 02 — Mapa funcional

**Objetivo:** producir el `functional_map.md` del workspace y los YAML de tracking por funcionalidad, combinando análisis determinístico (scripts) + juicio semántico (agente `functional-classifier`) + validación humana.

**Prerrequisito:** workflow `01-bootstrap.md` cerrado sin bloqueos.

---

## Paso 1 — Ejecutar scripts de scanner

Corré los dos scripts PowerShell en este orden. Usá la herramienta Bash con `pwsh` (o `powershell` si el sistema no tiene 7+).

### 1.1 — Hashing

```bash
pwsh -NoProfile -File "<plugin-root>/skills/document-xpp/scripts/Compute-XppHashes.ps1" `
  -SourcePath "<XppSource>" `
  -OutputPath "<workspace>/_tracking"
```

Efecto esperado:
- Crea `<workspace>/_tracking/hashes.csv`.
- Si ya existía, lo rota a `<workspace>/_tracking/hashes.previous.csv`.

### 1.2 — Inventario

```bash
pwsh -NoProfile -File "<plugin-root>/skills/document-xpp/scripts/Build-XppInventory.ps1" `
  -SourcePath "<XppSource>" `
  -OutputPath "<workspace>/_tracking"
```

Efecto esperado:
- Crea `<workspace>/_tracking/inventory.csv` con columnas: `file, class, parent, interfaces, methods_count, prefix`.
- Crea `<workspace>/_tracking/dependencies.csv` con columnas: `from_class, to_class, kind` donde `kind ∈ {extends, implements, uses, calls}`.

Si cualquiera de los scripts falla, **detené el flujo** e informá el error al usuario. No intentes reimplementar el parseo vos mismo.

---

## Paso 2 — (Sólo modo `actualizar` o `agregar-*`) — Diff de hashes

Si existe `<workspace>/_tracking/hashes.previous.csv`:

1. Cargá ambos CSV en memoria: `hashes.csv` (actual) y `hashes.previous.csv` (anterior).
2. Derivá tres conjuntos por comparación de la columna `file`:
   - **modificados** — mismo `file`, `md5` distinto.
   - **nuevos** — `file` está en actual, ausente en previo.
   - **eliminados** — `file` está en previo, ausente en actual.
3. Para cada `<workspace>/_tracking/funcionalidades/*.yaml`:
   - Si alguna clase referenciada está en modificados o eliminados, marcar `status: desactualizado`.
   - Caso contrario, mantener `status: actualizado`.
4. Los archivos **nuevos** quedan como huérfanos. Se presentan al usuario en el Paso 5.

En modo `nuevo`, saltá este paso.

---

## Paso 3 — Delegar al agente `functional-classifier`

Invocá el subagente con `Agent` y `subagent_type: functional-classifier`. Pasale en el prompt:

- **Path al workspace** (para que lea los CSV directamente).
- **Modo de sesión** (`nuevo` / `actualizar` / `agregar-independiente` / `agregar-relacionado`).
- **Funcionalidades existentes** (si las hay) — listá los `slug` + `name` + `description` de los YAML bajo `_tracking/funcionalidades/`.
- **Rutas de inputs opcionales registrados** (scope docs + manuales) — el agente puede leerlos si los necesita.
- **Nombre del producto/módulo** — preguntale al usuario si no fue provisto en bootstrap.

El agente devuelve una **propuesta de mapa funcional** en JSON estructurado (ver contrato en `agents/functional-classifier.md`). No interpretes libremente la salida — usá el JSON como input del Paso 4.

---

## Paso 4 — Validación humana del mapa

Presentá la propuesta del agente al usuario con `AskUserQuestion`. Formato recomendado:

```
El agente propuso los siguientes grupos funcionales:

1. <Nombre grupo> — <N clases> (<infijos detectados>)
2. <Nombre grupo> — <N clases> (<infijos detectados>)
...

¿Aceptás la propuesta, querés ajustar nombres/agrupaciones, o reclasificar manualmente?
```

Opciones a ofrecer:
- **Aceptar** — persistir tal cual.
- **Ajustar** — el usuario te dicta cambios puntuales (renombrar grupo, mover clases, fusionar grupos). Aplicás y confirmás.
- **Rehacer** — volver al Paso 3 con pistas adicionales del usuario.

No avances al Paso 5 hasta que el usuario diga **"aceptar"** (o equivalente inequívoco).

---

## Paso 5 — Resolver archivos huérfanos (si los hubiera)

Sólo aplica en modo `actualizar` o `agregar-*` cuando el Paso 2 detectó archivos nuevos.

Por cada huérfano, preguntá con `AskUserQuestion`:

```
Archivo nuevo detectado: <path relativo>
¿A qué funcionalidad lo asigno?
  a) <funcionalidad existente A>
  b) <funcionalidad existente B>
  ...
  n) Nueva funcionalidad independiente
  n+1) Nueva funcionalidad relacionada con <X>
  skip) Ignorar por ahora
```

Aplicá la decisión:
- Si es una funcionalidad existente: agregá la clase al YAML correspondiente.
- Si es nueva: creá un `<slug>.yaml` nuevo con el template.

---

## Paso 6 — Persistir artefactos

Generá / actualizá:

### 6.1 — `<workspace>/_tracking/funcionalidades/<slug>.yaml` (uno por funcionalidad)

Usá `templates/tracking-funcionalidad.yaml.tpl` como base. Schema en `references/tracking-schema.md`.

Campos clave:
- `name`, `slug`, `description`
- `created_at`, `last_updated`
- `status` — `nueva` si se creó ahora, `actualizado` si el diff no afectó clases, `desactualizado` si sí.
- `classes` — lista de `{ file, role }` donde `role ∈ {service, entity, controller, dto, helper, other}` (el classifier asigna rol).
- `inputs_registered` — scope/manuals/previous_diagrams (vienen de bootstrap).
- `artifacts` — vacío en M1 (los diagramas llegan desde M2).

### 6.2 — `<workspace>/functional_map.md` (human-readable)

Pivote del flujo. Estructura:

```markdown
# Mapa funcional — <Nombre del producto>

> Generado: <ISO-8601>
> Plugin: document-xpp@0.1.0
> Modo de sesión: <modo>

## <Nombre del grupo 1>

**Descripción:** <una línea>

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `<NombreClaseA>` | `<NombreClaseB>`, `<NombreClaseC>` | `SalesTable`, `Global` |
| ... | ... | ... |

## <Nombre del grupo 2>

...
```

Las referencias internas salen de `dependencies.csv` filtrando `to_class` que existen en `inventory.csv`. Las externas son las que NO están en el inventario **y** no aparecen en `references/exclusion-list.md`.

---

## Paso 7 — Confirmación final

Imprimí al usuario:

- Ruta del `functional_map.md`.
- Cantidad de funcionalidades persistidas + su status.
- Próxima fase: **03 — Diagramas de clases (M2, no disponible todavía)**.

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/functional_map.md` existe y refleja el mapa validado.
- `<workspace>/_tracking/funcionalidades/*.yaml` existen (uno por grupo) con status correcto.
- `<workspace>/_tracking/hashes.csv` + `inventory.csv` + `dependencies.csv` están al día.

M1 cierra acá. Fases 3–5 se entregan en M2, M3, M4.
