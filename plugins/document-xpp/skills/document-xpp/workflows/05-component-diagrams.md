# Workflow 05 — Diagramas de componentes C4

**Objetivo:** producir un diagrama C4 Component conceptual (Nivel 1, módulo completo) y un diagrama detallado por grupo funcional (Nivel 2), combinando los YAMLs de tracking de M2 + el agente `c4-component-writer` + validación humana.

**Prerrequisito:** workflows `01-bootstrap.md` y `02-functional-map.md` cerrados sin bloqueos. El workspace debe tener `_tracking/manifest.yaml` y al menos un `_tracking/funcionalidades/<slug>.yaml`. Se recomienda tener Fase 3 completada (`diagram_candidates/` presentes) — ver Paso 1.

---

## Paso 1 — Verificar diagram_candidates

La Fase 5 deriva las relaciones cross-grupo de los `diagram_candidates/*.yaml` (generados por Fase 3). Si no existen, corré el script primero:

1. Verificá si existe `<workspace>/_tracking/diagram_candidates/` con al menos un YAML.
2. Si NO existe o está vacío:
   ```bash
   python "<plugin-root>/skills/document-xpp/scripts/build_class_diagrams.py" \
     --workspace "<workspace>"
   ```
   Si el script falla, detené el flujo. No improvises candidatos — la Fase 5 necesita `external_refs[]` que sólo el script puede emitir correctamente.
3. Si el script corre bien pero el DBML no está en el manifest, el script lo avisa pero continúa (para C4 no es bloqueante — las relaciones vienen de las dependencias X++, no del DBML).

---

## Paso 2 — Alcance parcial (sólo en modo `actualizar` / `agregar-*`)

En modo `nuevo`, generás todos los grupos. En modos incrementales:

1. Leé los `funcionalidades/<slug>.yaml` y listá los `slug` con `status: desactualizado` o `status: nueva`.
2. Presentá la lista al usuario con `AskUserQuestion`:

   ```
   Funcionalidades con cambios o nuevas desde la última corrida:
     1) <slug-a> (desactualizado)
     2) <slug-b> (nueva)
     ...

   ¿Regenero los diagramas C4 de todas, o elegís un subconjunto?
   También regeneraré el Nivel 1 (conceptual) — cambia cuando cambia cualquier grupo.
   ```

3. Guardá la decisión como `grupos_a_regenerar: [slug-a, slug-b, ...]`. El Nivel 1 se regenera siempre que haya al menos un grupo a regenerar.

En modo `nuevo`: `grupos_a_regenerar` = todos los grupos.

---

## Paso 3 — Generar Nivel 1 (conceptual)

Invocá el agente con `Agent` y `subagent_type: c4-component-writer`. Pasale:

- `level`: `"conceptual"`
- `funcionalidades_dir`: `<workspace>/_tracking/funcionalidades/`
- `candidates_dir`: `<workspace>/_tracking/diagram_candidates/`
- `puml_output_path`: `<workspace>/diagrams/components/conceptual.puml`
- `template_path`: `<plugin-root>/skills/document-xpp/templates/component-diagram-l1.puml.tpl`
- `prompt_path`: `<plugin-root>/skills/document-xpp/prompts/05-component-conceptual.md`
- `workspace_path`: `<workspace>`

El agente devuelve un JSON con (ver contrato en `agents/c4-component-writer.md`):
- `puml_path`, `components_rendered`, `relations_rendered`, `omitted_groups[]`, `warnings[]`

Presentá al usuario con `AskUserQuestion` (ver formato en Paso 5).

---

## Paso 4 — Generar Nivel 2 (por grupo)

Para cada `slug` en `grupos_a_regenerar`, invocá el agente secuencialmente:

- `level`: `"detailed"`
- `funcionalidades_dir`: `<workspace>/_tracking/funcionalidades/<slug>.yaml`
- `candidates_dir`: `<workspace>/_tracking/diagram_candidates/<slug>.yaml`
- `puml_output_path`: `<workspace>/diagrams/components/<slug>/detailed.puml`
- `template_path`: `<plugin-root>/skills/document-xpp/templates/component-diagram-l2.puml.tpl`
- `prompt_path`: `<plugin-root>/skills/document-xpp/prompts/05-component-detailed.md`
- `workspace_path`: `<workspace>`

Ejecutá un agente por grupo de forma secuencial. Presentá cada resultado al usuario antes de avanzar al siguiente grupo (Paso 5).

---

## Paso 5 — Validación humana por diagrama

Por cada `.puml` generado (Nivel 1 primero, luego Nivel 2 en orden):

```
Diagrama: <ruta relativa al workspace>
Nivel: Conceptual / Detallado (<slug>)
Componentes: <N>  |  Relaciones: <M>
Warnings del agente:
  - <warning 1>
  - ...
```

Opciones con `AskUserQuestion`:
- **Aceptar** — pasar al siguiente diagrama.
- **Ajustar** — el usuario describe la corrección. Reinvocás el agente con las instrucciones adicionales como override en el prompt.
- **Rehacer** — volver al paso de invocación del agente desde cero.

Los `warnings[]` de grupos pequeños (< 5 clases) NO son errores. El usuario decide si el Nivel 2 es útil o no para ese grupo.

---

## Paso 6 — Actualizar tracking de funcionalidades

Por cada grupo procesado, actualizá `_tracking/funcionalidades/<slug>.yaml`:

- `artifacts.component_diagrams.level_1_node_in` = `"diagrams/components/conceptual.puml"`
- `artifacts.component_diagrams.level_2` = `"diagrams/components/<slug>/detailed.puml"`
- `last_updated` = ahora (ISO-8601 UTC)
- `status` = `actualizado` (si era `desactualizado` o `nueva`)

Para el Nivel 1 (conceptual.puml), actualizá `level_1_node_in` en TODOS los grupos del workspace, no sólo en los que regeneraste — todos "participan" del diagrama conceptual.

---

## Paso 7 — Resumen al usuario

Imprimí:

- Cantidad de diagramas generados (Nivel 1: 1, Nivel 2: N).
- Grupos conservados sin regenerar (modo incremental).
- Warnings agregados.
- Ruta de `functional_map.md` si lo actualizaste.
- Próxima fase: **04 — Diagramas de secuencia (M4, no disponible todavía)**.

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/diagrams/components/conceptual.puml` existe y está actualizado.
- `<workspace>/diagrams/components/<slug>/detailed.puml` existe para cada grupo regenerado.
- `<workspace>/_tracking/funcionalidades/<slug>.yaml` tiene `artifacts.component_diagrams.*` populados.
