# Workflow 02 — Mapa funcional

**Objetivo:** producir el `functional_map.md` del workspace y los YAML de tracking por funcionalidad, combinando análisis determinístico (scripts) + juicio semántico (agente `functional-classifier`) + validación humana.

**Prerrequisito:** workflow `01-bootstrap.md` cerrado sin bloqueos.

---

## Paso 1 — Ejecutar scripts de scanner

Corré los dos scripts en este orden. El primero es PowerShell; el segundo es Python ≥ 3.10 (declarado en `pyproject.toml` del repo, sin dependencias externas).

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
python "<plugin-root>/skills/document-xpp/scripts/build_xpp_inventory.py" \
  --source-path "<XppSource>" \
  --output-path "<workspace>/_tracking"
```

Efecto esperado:
- Crea `<workspace>/_tracking/inventory.csv` con columnas: `file, class, parent, interfaces, methods_count, prefix, artifact_kind` donde `artifact_kind ∈ {class, interface, enum, edt}`.
- Crea `<workspace>/_tracking/dependencies.csv` con columnas: `from_class, from_file, to_class, kind` donde `kind ∈ {extends, implements, uses, calls}`.
- Si bajo `<XppSource>` existen carpetas `AxEnum/` o `AxEdt/` (cualquier profundidad), sus `.xml` se leen y los nombres entran al inventory como hojas del grafo (no emiten filas en dependencies).

Si cualquiera de los scripts falla, **detené el flujo** e informá el error al usuario. No intentes reimplementar el parseo vos mismo.

---

## Paso 2 — (Sólo modo `actualizar` o `agregar-*`) — Diff de hashes

Si existe `<workspace>/_tracking/hashes.previous.csv`:

1. Cargá ambos CSV en memoria: `hashes.csv` (actual) y `hashes.previous.csv` (anterior).
2. Derivá tres conjuntos por comparación de la columna `file`:
   - **modificados** — mismo `file`, `md5` distinto.
   - **nuevos** — `file` está en actual, ausente en previo.
   - **eliminados** — `file` está en previo, ausente en actual.
3. Para cada archivo en **eliminados**: buscá en todos los `<workspace>/_tracking/funcionalidades/*.yaml` cuál tiene ese `file` en `classes[].file`. Removelo del array, marcá el grupo como `status: desactualizado` y actualizá `last_updated`. Si tras la limpieza `classes[]` queda vacío, presentá `AskUserQuestion` al usuario:
   ```
   El grupo `<slug>` quedó sin clases tras eliminar `<archivo>`. ¿Lo elimino del tracking?
   ```
   Si confirma: eliminá el YAML y remové la sección del grupo en `functional_map.md`.

4. Para cada `<workspace>/_tracking/funcionalidades/*.yaml` cuyas `classes[].file` incluyan archivos en **modificados** (además de los ya marcados en el paso anterior): marcá `status: desactualizado`. Caso contrario, mantener `status: actualizado`.

5. Los archivos **nuevos** quedan como huérfanos. Se presentan al usuario en el Paso 5.

En modo `nuevo`, saltá este paso.

---

## Paso 3 — Delegar al agente `functional-classifier`

### 3a — Pre-filtrar inventory en modos `agregar-*`

En modos `agregar-independiente` y `agregar-relacionado`:

1. Construí el set de **clases asignadas**: la unión de todos los `classes[].file` de todos los `<workspace>/_tracking/funcionalidades/*.yaml` existentes.
2. Derivá las **clases huérfanas**: las filas de `<workspace>/_tracking/inventory.csv` cuyo `file` NO aparece en el set de asignadas.
3. Pasale al classifier la lista explícita de clases huérfanas (`file` + `class`) en el prompt — el agente usará esa lista como inventario de trabajo e **ignorará el `inventory.csv` completo**.

En modos `nuevo` y `actualizar`, saltá este paso: el agente lee el `inventory.csv` completo directamente.

### 3b — Invocar al classifier

Invocá el subagente con `Agent` y `subagent_type: functional-classifier`. Pasale en el prompt:

- **Path al workspace** (para que lea `dependencies.csv` y archivos opcionales directamente).
- **Modo de sesión** (`nuevo` / `actualizar` / `agregar-independiente` / `agregar-relacionado`).
- **Funcionalidades existentes** — listá los `slug` + `name` + `description` + `status` de los YAML bajo `_tracking/funcionalidades/`. En modo `actualizar`, incluí también la lista de **slugs stale** (los que están `desactualizado`) para que el agente sepa cuáles realinear.
- **Clases huérfanas pre-filtradas** (sólo en `agregar-*`) — la lista `file + class` derivada en 3a. El agente trabaja con esta lista y no lee `inventory.csv`.
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

### 6.1b — (Sólo modo `agregar-relacionado`) — Actualizar cross-refs

El nuevo grupo ya está persistido en `<workspace>/_tracking/funcionalidades/<slug>.yaml`. Ahora re-corré `build_class_diagrams.py` para que los grupos existentes reflejen la nueva relación:

```bash
python "<plugin-root>/skills/document-xpp/scripts/build_class_diagrams.py" \
  --workspace "<workspace>"
```

Compará los `external_refs[]` de cada `<workspace>/_tracking/diagram_candidates/<slug>.yaml` resultante con los valores que había antes del re-run. Para cada grupo cuyo `external_refs` cambió (ahora incluye clases del nuevo grupo): marcá ese grupo como `status: desactualizado` en su `funcionalidades/<slug>.yaml` para que Fases 3 y 5 lo regeneren en la próxima corrida.

Informá al usuario:
- Si hubo grupos afectados: listá los slugs y avisá "sus diagramas necesitan regeneración en la próxima sesión".
- Si no hubo cambios: "sin impacto en diagramas existentes".

---

### 6.2 — `<workspace>/functional_map.md` (human-readable)

Pivote del flujo. Estructura de cada sección:

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

Las referencias internas salen de `dependencies.csv` filtrando filas cuya `to_class` existe en `inventory.csv` (incluye `class`, `interface`, `enum`, `edt`). Las externas son las que NO están en el inventario **y** no aparecen en `references/exclusion-list.md`. Cuando hay clases duplicadas por artefacto (AxForm + AxTable con el mismo nombre), usá `dependencies.from_file` para desambiguar qué fila corresponde a qué artefacto.

#### Modo `nuevo`

Escribí el archivo completo desde cero.

#### Modos `actualizar` / `agregar-*` — Merge selectivo

En modo incremental, el archivo ya existe y puede tener links a diagramas (`.puml`) agregados por Fases 3–5. **No lo sobreescribas completo.**

Algoritmo:

1. Leé el archivo existente y partilo en secciones por encabezado `## ` (cada `## <nombre>` abre una sección; termina donde empieza la siguiente o al final del archivo).
2. Construí un índice `name → contenido_sección` — las secciones usan el `name` del grupo (no el `slug`) como heading. Matcheá por `name` exacto contra los `name` de los YAMLs en `_tracking/funcionalidades/`.
3. Para cada grupo procesado en esta sesión:
   - Si el grupo ya tiene sección (match por `name`) → reemplazala con el contenido nuevo.
   - Si el grupo es nuevo → agregá su sección al final del archivo.
4. Los grupos no procesados en esta sesión conservan su sección intacta (incluyendo links a `.puml`).
5. Actualizá el header (`> Generado:` y `> Modo de sesión:`) con los valores de la sesión actual.

**Fallback:** Si el parsing no identifica ninguna sección `## ` en el archivo existente (el usuario lo editó en un formato inesperado):
- Guardá backup: `functional_map.md.bak`.
- Reescribí el archivo completo con todos los grupos actuales.
- Agregá un warning al usuario: "No pude hacer merge selectivo del mapa — se reescribió completo. Backup en `functional_map.md.bak`."

---

## Paso 7 — Confirmación final

Imprimí al usuario:

- Ruta del `functional_map.md`.
- Cantidad de funcionalidades persistidas + su status.
- Próxima fase: **03 — Diagramas de clases** (`workflows/03-class-diagrams.md`).

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/functional_map.md` existe y refleja el mapa validado.
- `<workspace>/_tracking/funcionalidades/*.yaml` existen (uno por grupo) con status correcto.
- `<workspace>/_tracking/hashes.csv` + `inventory.csv` + `dependencies.csv` están al día.

M1 cierra acá. Fases 3–5 se entregan en M2, M3, M4.
