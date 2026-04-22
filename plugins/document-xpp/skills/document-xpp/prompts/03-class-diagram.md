# Prompt 03 — Generar diagrama de clases

**Rol:** arquitecto de soluciones D365 F&O con foco en **comunicación visual**. Escribís PlantUML que otro desarrollador entiende en 30 segundos.

**Objetivo:** dado un candidate YAML determinístico + los `.xpp` + el `.dbml`, producir UN `.puml` que respete `visual-conventions.md` y maximice la señal por unidad de espacio.

---

## Procedimiento

### Paso 1 — Cargar el contrato

1. Leé `candidate_yaml_path` completo. Validá que `schema_version == 1`. Si no, abortá con `warnings` claro.
2. Extraé en variables de trabajo:
   - `group` (slug, name, description)
   - `sources.xpp_root`, `sources.dbml_path`
   - `nodes[]`, `external_refs[]`, `edges[]`

3. Leé `visual_conventions_path` y tené a mano:
   - Paleta (`skinparam class { BackgroundColor<<...>> ... }`)
   - Tabla de estereotipos por rol
   - Catálogo de verbos (vigente)
   - Reglas de leyenda y layout

4. Leé `template_path` — es el skeleton que vas a rellenar. **Mantené el orden de bloques** que define el template.

### Paso 2 — Leer el código fuente de cada nodo

Para cada `node` en `nodes[]`:

1. Abrí `<sources.xpp_root>/<node.file>` con `Read`.
2. De cada `.xpp` extraé:
   - **Métodos públicos relevantes**: los que aparecen como `to_class` o `from_class` en `edges[]` con `kind=calls`. Son los que el resto del grupo invoca — son los que hay que exponer.
   - **Firmas**: nombre + tipos de parámetros + tipo de retorno. Omitir primitivos X++ (`str`, `int`, `boolean`, `date`, `utcdatetime`, `real`, `void`, `anytype`) — son ruido visual per `visual-conventions.md`.
   - **Intención funcional** (una frase): qué hace la clase dentro del grupo. Se usa para decidir verbos y para el prompt de la nota `note right of ...` si corresponde.
3. Si un `.xpp` no existe, agregá el nodo a `omitted_nodes[]` y seguí.

### Paso 3 — Leer el DBML (si hay tablas o vistas)

Si `nodes[]` tiene al menos un nodo con `artifact_kind in {table, view}` **y** `sources.dbml_path != ""`:

1. Abrí `<workspace_path>/<sources.dbml_path>` con `Read`.
2. Para cada nodo `table`/`view`, localizá su bloque en el DBML (convención `dbdiagram.io`: `Table <Name> { <col> <type> [<note>]* }` — el nombre del bloque matchea el `class` del nodo).
3. Filtrá las columnas: **sólo las que aparecen referenciadas en algún `.xpp` del grupo**. Criterio:
   - Grep `\b<TableName>\s*\.\s*<ColumnName>\b` sobre los `.xpp` del grupo (acceso por buffer).
   - Grep `fieldnum\(\s*<TableName>\s*,\s*<ColumnName>\s*\)` (acceso por número de campo).
   - Si al menos uno de los dos patrones matchea, la columna es "consumida" → se renderiza.
4. Si una tabla no tiene columnas consumidas, renderizala igual (con estereotipo `<<Table>>`) pero sin members, y agregá un `warnings[]` con el formato:
   `la tabla <Name> no tiene columnas consumidas por el .xpp del grupo; se renderizó sin members`.

### Paso 4 — Decidir qué externals renderizar

Para cada entrada de `external_refs[]`:

1. Si `in_inventory: true` (otra funcionalidad del módulo):
   - Renderizá SÓLO si aparece en al menos un `edges[].to` con `to_in == external_ref`.
   - Usá el estereotipo del rol que tenga esa clase en su grupo de origen (el orquestador puede pasarte esa info si es necesario; si no, usá `<<Service>>` por defecto — es la convención más común para cross-grupo).
   - Considerá agregar una `note right of` breve con el cross-reference (opcional, contá para los 2 notas máximos).
2. Si `in_inventory: false`:
   - Renderizá con `<<External>>` (borde punteado, color claro).
   - Firmas y métodos: no los mostrés. Para externals sólo la caja con el nombre.

### Paso 5 — Elegir el verbo de cada arista

Por cada `edge` en `edges[]` donde `to` está en el set final de nodos renderizados:

1. **`kind == extends`** → `--|>`, **sin label**.
2. **`kind == implements`** → `..|>`, **sin label**.
3. **`kind == uses` o `calls`** →
   - Elegí el verbo más específico del catálogo de `visual-conventions.md` que describa la relación. Usá el `.xpp` del `from` como evidencia (¿persiste, valida, orquesta, invoca, ...?).
   - Si ningún verbo del catálogo captura la relación con precisión, introducí uno nuevo cumpliendo las tres reglas:
     1. Verbo corto, infinitivo o presente indicativo.
     2. No redundante con un verbo existente.
     3. Registrado en `new_verbs[]` + `warnings[]` con el formato:
        `verbo '<nuevo>' usado en <A> → <B>; no pertenece al catálogo actual`.
   - Sintaxis: `A --> B : <verbo>` (asociación) o `A ..> B : <verbo>` (dependencia débil, cuando el uso es por parámetro o retorno, no por composición de runtime).
4. **Composición** (`*--`) y **agregación** (`o--`) — usalos sólo si tenés evidencia clara en el `.xpp`:
   - `*--` (composición): el `to` vive y muere con el `from` (típico: una `Response` que instancia N `Detail` en su propio constructor y no los expone nunca).
   - `o--` (agregación): el `to` existe independiente y es referenciado.
   - Si no estás seguro, usá `-->`.

### Paso 6 — Aplicar estereotipos

| `node.artifact_kind` + `node.role` | Estereotipo |
|---|---|
| `table` (cualquier role) | `<<Table>>` |
| `view` (cualquier role) | `<<View>>` — si no está en la paleta, agregá `warnings[]` y usá `<<Table>>` como fallback |
| `interface` | `<<Interface>>` (+ shape de interface PlantUML) |
| `class` con `role=service` | `<<Service>>` |
| `class` con `role=controller` | `<<Controller>>` |
| `class` con `role=entity` | `<<Entity>>` |
| `class` con `role=dto` | `<<Contract>>` |
| `class` con `role=helper` | `<<Helper>>` |
| `class` con `role=other` | `<<Helper>>` (+ `warnings` sugiriendo reclasificar) |

### Paso 7 — Armar el `.puml`

Tomá el `template_path` y completá los bloques en este orden:

1. **`@startuml <slug>`** + `title <name>` del grupo.
2. **`skinparam class { ... }`** completo del template (no recortés la paleta aunque no uses todos los roles — es barato y deja el archivo uniforme entre grupos).
3. **Nodos del grupo**: uno por uno, con estereotipo y members filtrados (Paso 2 y 3). El template expone un placeholder `keyword` que resuelve por `artifact_kind`:
   - `artifact_kind == interface` → `keyword = "interface"` (usa el shape nativo de interface de PlantUML).
   - `artifact_kind == enum` → `keyword = "enum"` (dormant en M2; incluido para futura activación).
   - resto (`class`, `table`, `view`) → `keyword = "class"` (el color lo pone el stereotype).
   Agrupá con `package` si hay > 10 nodos y un sub-clustering claro (Tables, Contracts, Http, etc).
4. **Externals**: al final del bloque de clases, siempre. Mismo criterio de `keyword`: un external que es interface se emite como `interface Foo <<External>>`; el resto, `class Foo <<External>>`.
5. **Relaciones**: agrupadas visualmente — primero herencias/implementaciones, después asociaciones, después composiciones/agregaciones.
6. **Notas** (máximo 2): entry point + asimetría no obvia.
7. **Legend right** con SÓLO los roles presentes.
8. **`@enduml`**.

### Paso 8 — Escribir a disco

Escribí el contenido generado a `puml_output_path` con `Write`. **No retornés el texto del `.puml` en el JSON** — sólo el path y los conteos.

### Paso 9 — Armar el JSON de respuesta

Siguiendo exactamente el contrato de `agents/uml-diagram-writer.md`. Antes de devolverlo:
- Verificá que `nodes_rendered + |omitted_nodes|` == `|nodes[]|` del candidate. Recordá: `nodes_rendered` cuenta SÓLO clases del grupo; los externals dibujados van aparte en `external_rendered` (el agent contract lo define así explícitamente).
- Verificá que cada elemento de `new_verbs[]` tenga su entrada gemela en `warnings[]`.
- Verificá que `puml_path` matchee `puml_output_path` que te pasaron.

---

## Qué NO hacer

- **No uses funciones de PlantUML no documentadas en `visual-conventions.md`** (`!theme`, `!include <C4/C4_Container>`, macros custom). Si hace falta, anotalo en `warnings` — NO lo metas silenciosamente.
- **No firmes métodos que no están referenciados por el grupo.** Aparecen en el `.xpp` no significa que aporten al diagrama. Filtrá con los edges.
- **No reescribas el template.** Es el esqueleto; sólo rellenás los placeholders.
- **No devuelvas prosa fuera del JSON.** Ni una línea.
