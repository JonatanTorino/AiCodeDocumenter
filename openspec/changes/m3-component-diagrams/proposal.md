# Proposal: M3 — Diagramas de Componentes C4

## Intent

Habilitar la Fase 5 del plugin `document-xpp`: generar diagramas de componentes C4 en dos niveles de abstracción (módulo completo y por grupo funcional). Cierra el gap marcado en SKILL.md como "M3 — no disponible todavía".

## Scope

### In Scope
- `workflows/05-component-diagrams.md` — orquestación Fase 5
- `prompts/05-component-conceptual.md` — procedimiento Nivel 1 (módulo completo)
- `prompts/05-component-detailed.md` — procedimiento Nivel 2 (por grupo)
- `references/c4-plantuml-usage.md` — referencia sintaxis C4-PlantUML stdlib
- `templates/component-diagram-l1.puml.tpl` — skeleton Nivel 1
- `templates/component-diagram-l2.puml.tpl` — skeleton Nivel 2
- `agents/c4-component-writer.md` — agente especializado C4 (separado de UML)
- Rename `agents/diagram-writer.md` → `agents/uml-diagram-writer.md`
- Updates: `SKILL.md`, `workflows/03-class-diagrams.md` (referencias y estado)

### Out of Scope
- Fase 4 (secuencia) — M4
- Script determinístico intermedio (`component_candidates/*.yaml`) — innecesario
- `anthropic-skills:c4-plantuml` — no habilitado; usar plantuml-stdlib directamente

## Capabilities

### New Capabilities
- `component-diagrams-c4`: Generación de diagramas C4 Component en dos niveles: Nivel 1 = un componente por grupo funcional con relaciones cross-grupo (`diagrams/components/conceptual.puml`); Nivel 2 = sub-componentes semánticos por grupo sin bajar a clases individuales (`diagrams/components/<slug>/detailed.puml`).

### Modified Capabilities
- None

## Approach

Sin script determinístico nuevo. Los `diagram_candidates/<slug>.yaml` (generados por M2) ya contienen `external_refs[].{in_inventory, other_group_slug}` = relaciones cross-grupo. El workflow 05 pasa esos YAMLs + `funcionalidades/*.yaml` directamente al agente `c4-component-writer`, que usa sintaxis C4-PlantUML stdlib (`!include C4_Component.puml`). El agente `uml-diagram-writer` (rename de `diagram-writer`) queda sin cambios funcionales.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `plugins/document-xpp/skills/document-xpp/workflows/05-component-diagrams.md` | New | Workflow Fase 5 completo |
| `plugins/document-xpp/skills/document-xpp/prompts/05-component-conceptual.md` | New | Procedimiento Nivel 1 |
| `plugins/document-xpp/skills/document-xpp/prompts/05-component-detailed.md` | New | Procedimiento Nivel 2 |
| `plugins/document-xpp/skills/document-xpp/references/c4-plantuml-usage.md` | New | Referencia sintaxis C4 |
| `plugins/document-xpp/skills/document-xpp/templates/component-diagram-l1.puml.tpl` | New | Skeleton Nivel 1 |
| `plugins/document-xpp/skills/document-xpp/templates/component-diagram-l2.puml.tpl` | New | Skeleton Nivel 2 |
| `plugins/document-xpp/agents/c4-component-writer.md` | New | Agente C4 |
| `plugins/document-xpp/agents/diagram-writer.md` | Rename → `uml-diagram-writer.md` | Nomenclatura consistente |
| `plugins/document-xpp/skills/document-xpp/SKILL.md` | Modified | Habilitar Fase 5 + ref rename |
| `plugins/document-xpp/skills/document-xpp/workflows/03-class-diagrams.md` | Modified | Paso 8 next-phase correcto |

## Risks

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| `diagram_candidates` no existen si Fase 3 no corrió | Media | Workflow 05 verifica su existencia y corre `build_class_diagrams.py` si faltan |
| Nivel 2 visualmente redundante con diagrama de clases en grupos pequeños (< 5 clases) | Media | Prompt prohíbe exponer clases individuales — abstracción por cluster semántico |
| Rename `diagram-writer` rompe referencias en archivos no relevados | Baja | Grep completo antes del rename para cubrir todos los consumidores |

## Rollback Plan

1. `git revert` o `git rm` de los 7 archivos nuevos.
2. `git mv agents/uml-diagram-writer.md agents/diagram-writer.md`.
3. Revertir `SKILL.md` y `workflows/03-class-diagrams.md` a su estado de M2.
4. El tracking schema NO cambia — `artifacts.component_diagrams` ya existía en M2, simplemente queda vacío.

## Dependencies

- Workflow 02 y 03 ejecutados al menos una vez (genera `funcionalidades/*.yaml` y `diagram_candidates/*.yaml`).

## Success Criteria

- [ ] `workflows/05-component-diagrams.md` ejecutable end-to-end sobre un workspace con Fases 1–3 completadas.
- [ ] `diagrams/components/conceptual.puml` generado y renderizable en VS Code con `visualization@melodic-software`.
- [ ] `diagrams/components/<slug>/detailed.puml` generado para cada grupo del módulo.
- [ ] `artifacts.component_diagrams.{level_1_node_in, level_2}` populados en todos los `funcionalidades/*.yaml`.
- [ ] Todas las referencias a `diagram-writer` en el codebase apuntan a `uml-diagram-writer`.
