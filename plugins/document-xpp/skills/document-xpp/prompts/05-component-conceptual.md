# Prompt 05-Conceptual — Generar diagrama de componentes C4 Nivel 1

**Rol:** arquitecto de soluciones D365 F&O con foco en **comunicación de arquitectura**. Generás un diagrama C4 Component que responde "¿cómo se organiza este módulo?" en 30 segundos.

**Objetivo:** dado el conjunto de `funcionalidades/*.yaml` + `diagram_candidates/*.yaml` de un workspace, producir UN `diagrams/components/conceptual.puml` con un componente por grupo funcional y las relaciones cross-grupo derivadas de los candidatos.

---

## Procedimiento

### Paso 1 — Cargar el contrato

1. Leé `references/c4-plantuml-usage.md` — tenés a mano los macros y reglas de sintaxis.
2. Leé `templates/component-diagram-l1.puml.tpl` — es el skeleton que vas a rellenar. **Mantené el orden de bloques.**

### Paso 2 — Leer todos los grupos funcionales

1. Glob `funcionalidades_dir/*.yaml`.
2. De cada YAML extraé: `slug`, `name`, `description`.
3. Construí la lista de componentes:
   - `alias` = `cmp_<slug_snake>` donde `slug_snake` es el `slug` normalizado a snake_case (reemplazá `-` por `_`). Ej: `license-management` → `cmp_license_management`.
   - `label` = `name` del YAML.
   - `description` = primera oración del `description`, máximo 80 caracteres.

### Paso 3 — Construir el mapa de relaciones cross-grupo

1. Para cada `diagram_candidates/<slug>.yaml`:
   - Filtrá `external_refs[]` donde `in_inventory: true`. Cada entrada identifica un par de grupos relacionados.
   - Por cada `external_ref` con `in_inventory: true`, buscá en `edges[]` las aristas con `to_in: external_ref` cuyo `to` coincida con esa clase. Normalizá `slug` y `other_group_slug` a snake_case para los aliases.
   - Relación: `from = cmp_<slug_snake>` → `to = cmp_<other_group_slug_snake>`.
2. Deduplicá pares `(from, to)` — emitís UNA relación por par direccional.
3. Para el label de cada relación: derivalo del `kind` de los `edges[]` que cruzan ese par de grupos. Si la mayoría son `kind: uses` → `"usa"`; si hay `kind: calls` → `"invoca"`. Usá el vocabulario de `visual-conventions.md`. Si no hay edges identificables, usá `"usa"` como default.
4. Si ningún grupo tiene `external_refs[].in_inventory: true`, registrá un `warnings[]` con `"ningún grupo tiene relaciones cross-grupo detectadas"` y generá el diagrama sin relaciones.

### Paso 4 — Rellenar el template

Tomá `component-diagram-l1.puml.tpl` y completá:
- `{{slug}}` → nombre del módulo en kebab-case (derivado del nombre del workspace o del manifest).
- `{{module_name}}` → nombre visible del módulo.
- `{{#components}}` → la lista construida en Paso 2.
- `{{#external_components}}` → grupos externos al boundary que aparecen como destino de relaciones. Para L1 NO son externales fuera del módulo — todos los grupos están dentro del `Container_Boundary`. Los `external_components` del template L1 quedan vacíos salvo que haya referencias a grupos que no tienen `funcionalidades/*.yaml` (incoherencia de datos — registrar en `warnings[]`).
- `{{#relations}}` → la lista construida en Paso 3.

### Paso 5 — Escribir a disco

Escribí el `.puml` a `puml_output_path` con `Write`. **No retornés el texto del `.puml` en el JSON** — sólo el path y los conteos.

### Paso 6 — Armar el JSON de respuesta

Siguiendo el contrato de `agents/c4-component-writer.md`:
- `level` = `"conceptual"`
- `group_slug` = `""`
- `components_rendered` = cantidad de `Component(...)` en el `.puml`
- `relations_rendered` = cantidad de `Rel(...)` en el `.puml`
- `omitted_groups[]` = grupos con YAML faltante o corrupto
- `warnings[]` = cualquier gotcha relevante

---

## Qué NO hacer

- **No bajes al nivel de clases.** Si ves clases en los YAML, ignoralas — el L1 sólo conoce grupos.
- **No inventes relaciones.** Sólo las que aparecen en `external_refs[].in_inventory: true`.
- **No reescribas el template.** Sólo rellenás los placeholders.
- **No devuelvas prosa fuera del JSON.**
