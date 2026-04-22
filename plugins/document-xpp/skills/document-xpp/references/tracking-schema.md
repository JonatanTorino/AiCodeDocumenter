# Tracking schema

Contrato de los archivos de estado que vive bajo `<workspace>/_tracking/`. Lo respetan los workflows, los agentes y los scripts. Cualquier cambio en este schema requiere actualización coordinada de todos los consumidores.

---

## `_tracking/manifest.yaml`

Metadata general del workspace. Un único archivo.

```yaml
workspace_version: 1                    # int — schema version; bump al romper compatibilidad
created_at: 2026-04-20T14:30:00Z        # ISO-8601 UTC — timestamp de la primera sesión `nuevo`
last_session_at: 2026-04-20T14:30:00Z   # ISO-8601 UTC — timestamp de la última ejecución del skill
sources:
  xpp_root: D:/src/License/XppSource    # path absoluto al XppSource usado en la última sesión
  dbml_path: dbml/license-schema.dbml   # string — ruta RELATIVA al workspace; "" si el user no aportó DBML
plugin_version: 0.1.0                    # version del plugin document-xpp que generó esta sesión
```

**Invariantes:**
- `created_at` NUNCA cambia después de la sesión inicial.
- `last_session_at` se actualiza en cada ejecución del skill.
- Si `workspace_version` del manifest no matchea con el esperado por el plugin instalado, el skill debe detectarlo y pedir migración antes de avanzar.
- `sources.xpp_root` es path **absoluto** (fuera del workspace). `sources.dbml_path` es **relativo** al workspace (el `.dbml` se copia adentro en Fase 1).
- `sources.dbml_path` vacío significa "el usuario no aportó DBML al hacer bootstrap". La Fase 3 (diagramas de clases) lo requiere y pedirá el archivo al iniciar si falta; al copiarlo, actualiza el manifest en ese momento.

---

## `_tracking/hashes.csv`

Barrido MD5 + metadata de todos los `.xpp` bajo `XppSource` al momento de la sesión actual.

**Generado por:** `scripts/Compute-XppHashes.ps1`.

**Columnas (header en la primera fila):**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `file` | string | Ruta relativa al `XppSource` con `/` como separador. |
| `size` | int | Tamaño en bytes. |
| `mtime` | int64 | Epoch Unix (segundos) del `LastWriteTimeUtc` del archivo. |
| `md5` | hex string | MD5 del contenido binario, lowercase. |

**Orden:** alfabético por `file` para garantizar diffs estables.

---

## `_tracking/hashes.previous.csv`

Idéntico schema que `hashes.csv`. Es el snapshot anterior, preservado al inicio de cada sesión `actualizar` o `agregar-*` para poder diffear.

- Se genera automáticamente al rotar `hashes.csv` → `hashes.previous.csv` dentro de `Compute-XppHashes.ps1`.
- En la primera sesión (`nuevo`), este archivo no existe.

---

## `_tracking/inventory.csv`

Lista de clases, interfaces, enums y EDTs encontrados por el parser en el último barrido.

**Generado por:** `scripts/build_xpp_inventory.py` (Python ≥ 3.10, stdlib).

**Columnas:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `file` | string | Ruta relativa al `XppSource` con `/`. |
| `class` | string | Nombre de la clase, interfaz, enum o EDT. |
| `parent` | string | Clase padre (vacío si no hereda, o `Common` para tablas; vacío para enums/EDTs). |
| `interfaces` | string | Interfaces implementadas, separadas por `;` (vacío para enums/EDTs). |
| `methods_count` | int | Cantidad total de métodos declarados (0 para enums/EDTs). |
| `prefix` | string | Primeros 3 caracteres del nombre (heurística; ignora la `I` inicial de interfaces). |
| `artifact_kind` | string | `class`, `interface`, `enum` o `edt`. |

**Notas:**
- Los enums y EDTs se leen desde `AxEnum/*.xml` y `AxEdt/*.xml` (cualquier subcarpeta bajo `SourcePath`), no de `.xpp`. Solo se extrae `<Name>`.
- El campo `artifact_kind` se agregó en M1.7 — consumidores anteriores que ignoren la última columna siguen siendo compatibles.

---

## `_tracking/dependencies.csv`

Grafo de dependencias inferido del análisis estático.

**Generado por:** `scripts/build_xpp_inventory.py`.

**Columnas:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `from_class` | string | Clase que declara la referencia. |
| `from_file` | string | Ruta relativa al `XppSource` (con `/`) del archivo donde se declara la referencia. |
| `to_class` | string | Clase referenciada. |
| `kind` | string | `extends`, `implements`, `uses` (`new X()`) o `calls` (`X::member`). |

**Notas:**
- `from_file` desambigua clases con mismo nombre pero distinto artefacto (p.ej. `AxnLicParameters` como AxForm y como AxTable emiten filas separadas).
- Los enums y EDTs no emiten filas aquí — son hojas del grafo.

---

## `_tracking/funcionalidades/<slug>.yaml`

**Un archivo por funcionalidad.** Lo genera el workflow 02 y lo actualizan workflows posteriores (M2+) cuando agreguen artefactos gráficos.

```yaml
name: Gestión de Suscripciones          # string — nombre visible, puede cambiar
slug: subscription                       # string — kebab-case ASCII — INMUTABLE una vez creado
description: >
  Ciclo de vida de las suscripciones: creación, renovación, cancelación,
  cambio de plan.
created_at: 2026-04-20T14:30:00Z         # ISO-8601 UTC
last_updated: 2026-04-20T14:30:00Z       # ISO-8601 UTC
status: nueva                            # nueva | actualizado | desactualizado

classes:
  - file: AxnLicSubscription/AxnLicSubscriptionService.xpp
    class: AxnLicSubscriptionService
    role: service
  - file: AxnLicSubscription/AxnLicSubscription.xpp
    class: AxnLicSubscription
    role: entity

inputs_registered:
  scope:
    - K:/docs/subscription-scope.md       # path absoluto; sólo se registra, NO se copia
  manuals:
    - K:/manuals/subscription-manual.md
  previous_diagrams:                      # si se aportaron, se COPIARON a <workspace>/adicionales/clases-previas/
    - K:/legacy/subscription-classes.puml

artifacts:
  class_diagram: ""                       # M2 — diagrams/classes/<slug>.puml
  sequence_diagrams: []                   # M4 — lista de { name, file }
  component_diagrams:
    level_1_node_in: ""                   # M3 — diagrams/components/conceptual.puml
    level_2: ""                           # M3 — diagrams/components/<slug>/detailed.puml
```

**Invariantes:**
- `slug` es la clave primaria. Renombrarlo equivale a eliminar y crear.
- `classes[].role` ∈ `{ service, entity, controller, dto, helper, other }`.
- `status` transiciones válidas:
  - `nueva` (creada en esta sesión) → `actualizado` (próxima sesión sin cambios) → `desactualizado` (próxima sesión con cambios) → `actualizado` (al regenerar artefactos) → …
- `artifacts.*` vacíos en M1; se van llenando en M2+ cuando los workflows correspondientes generen los `.puml`.

---

## `functional_map.md`

Documento Markdown human-readable, no es estado sino entregable visual. Se regenera desde los YAML por el workflow 02.

Estructura obligatoria:

```markdown
# Mapa funcional — <Nombre del producto>

> Generado: <ISO-8601 UTC>
> Plugin: document-xpp@<version>
> Modo de sesión: <modo>

## <Nombre del grupo>

**Descripción:** <una línea>
**Status:** <status>

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `ClaseA` | `ClaseB`, `ClaseC` | `SalesTable`, `CustTable` |
```

El encabezado con metadata permite diffear versiones del mapa entre sesiones.
