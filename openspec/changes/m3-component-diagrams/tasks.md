# Tasks: M3 — Diagramas de Componentes C4

> Paths relativos a `plugins/document-xpp/`.
> Fase 1 y 2 no tienen dependencias entre sí y pueden ejecutarse en paralelo.
> Fase 3 depende de Fase 2. Fase 4 depende de Fase 3. Fase 5 depende de todas.

---

## Fase 1: Rename uml-diagram-writer (9 archivos)

- [x] 1.1 Renombrar `agents/diagram-writer.md` → `agents/uml-diagram-writer.md`; actualizar `name:` y título interno de `diagram-writer` a `uml-diagram-writer`
- [x] 1.2 `skills/document-xpp/SKILL.md` — actualizar tabla de fases: ref `diagram-writer` → `uml-diagram-writer`; habilitar Fase 5 (quitar "no disponible todavía")
- [x] 1.3 `skills/document-xpp/workflows/03-class-diagrams.md` — Paso 4 y Paso 8: `diagram-writer` → `uml-diagram-writer`; Paso 8 next-phase: apuntar a Fase 5
- [x] 1.4 `skills/document-xpp/prompts/03-class-diagram.md` — línea 119: `diagram-writer` → `uml-diagram-writer`
- [x] 1.5 `skills/document-xpp/references/visual-conventions.md` — 3 ocurrencias: `diagram-writer` → `uml-diagram-writer`
- [x] 1.6 `skills/document-xpp/references/tracking-schema.md` — línea 152: `diagram-writer` → `uml-diagram-writer`
- [x] 1.7 `skills/document-xpp/scripts/build_class_diagrams.py` — docstring línea 6: `diagram-writer` → `uml-diagram-writer`
- [x] 1.8 `README.md` — árbol de agentes: renombrar `diagram-writer.md`; agregar `c4-component-writer.md`

---

## Fase 2: Fundamentos C4 (referencia + templates)

- [x] 2.1 Crear `skills/document-xpp/references/c4-plantuml-usage.md` — macros clave: `Component`, `Container_Boundary`, `Rel`, `Component_Ext`, `SHOW_LEGEND()`, `!include <C4/C4_Component.puml>`; diferencias con PlantUML UML
- [x] 2.2 Crear `skills/document-xpp/templates/component-diagram-l1.puml.tpl` — skeleton Nivel 1: `@startuml`, `!include`, `Container_Boundary`, `{{#components}} Component(...) {{/components}}`, `{{#relations}} Rel(...) {{/relations}}`, `SHOW_LEGEND()`
- [x] 2.3 Crear `skills/document-xpp/templates/component-diagram-l2.puml.tpl` — skeleton Nivel 2: igual que L1 pero con `{{#clusters}}` en lugar de `{{#components}}` y `Component_Ext` para externos

---

## Fase 3: Agente c4-component-writer

- [x] 3.1 Crear `agents/c4-component-writer.md` — persona (arquitecto C4), inputs del orquestador (funcionalidades_dir, candidates_dir, puml_output_path, template_path, prompt_path, workspace_path, level), tools (Read, Glob, Write), procedimiento (leer YAMLs → construir mapa → rellenar template → escribir .puml), contrato JSON estricto (`level`, `group_slug`, `puml_path`, `components_rendered`, `relations_rendered`, `omitted_groups[]`, `warnings[]`)

---

## Fase 4: Prompts y Workflow

- [x] 4.1 Crear `skills/document-xpp/prompts/05-component-conceptual.md` — pasos: cargar funcionalidades/*.yaml, leer diagram_candidates/*.yaml, construir mapa de componentes y relaciones cross-grupo desde `external_refs[].in_inventory=true`, rellenar template L1, escribir .puml, armar JSON de respuesta
- [x] 4.2 Crear `skills/document-xpp/prompts/05-component-detailed.md` — pasos: cargar funcionalidades/<slug>.yaml, leer diagram_candidates/<slug>.yaml, agrupar nodes[] en clusters semánticos por role/artifact_kind (tabla de mapping), rellenar template L2, agregar warning si < 5 clases, armar JSON de respuesta
- [x] 4.3 Crear `skills/document-xpp/workflows/05-component-diagrams.md` — Paso 1: verificar diagram_candidates (correr build_class_diagrams.py si faltan); Paso 2: alcance parcial (nueva/desactualizado vs todos); Paso 3: invocar c4-component-writer L1; Paso 4: invocar c4-component-writer L2 por grupo; Paso 5: validación humana por .puml; Paso 6: actualizar tracking `artifacts.component_diagrams`; Paso 7: resumen

---

## Fase 5: Verificación

- [x] 5.1 `grep -r "diagram-writer" plugins/` — debe devolver 0 resultados (rename completo) ✓ verificado
- [ ] 5.2 Ejecutar Workflow 05 contra workspace golden (`.validation/`); verificar que `conceptual.puml` renderiza en VS Code con `visualization@melodic-software`
- [ ] 5.3 Verificar `detailed.puml`: no contiene clases individuales (`grep "class " diagrams/components/*/detailed.puml` debe devolver 0); contiene al menos un cluster semántico por grupo
- [ ] 5.4 Verificar que `artifacts.component_diagrams.{level_1_node_in, level_2}` están populados en todos los `funcionalidades/*.yaml` del workspace golden
