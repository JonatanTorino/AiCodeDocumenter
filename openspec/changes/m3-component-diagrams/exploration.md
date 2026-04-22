## Exploration: m3-component-diagrams

### Current State

M2 cerrado y mergeado. El plugin soporta Fases 1–3 (bootstrap, mapa funcional, diagramas de clases). El SKILL.md ya marca "Fase 5 (C4) = M3 — no disponible todavía" y el workflow 03 termina citando "Próxima fase: 04 — Diagramas de componentes (C4 — M3)".

**Lo que ya existe y M3 puede aprovechar:**
- `_tracking/funcionalidades/<slug>.yaml` contiene `artifacts.component_diagrams.{level_1_node_in, level_2}` — los campos ya están en el schema de tracking-schema.md, solo están vacíos.
- `_tracking/diagram_candidates/<slug>.yaml` contiene `external_refs[].{in_inventory, other_group_slug}` — esto son exactamente las relaciones cross-grupo que alimentan el Nivel 1 conceptual.
- `.claude/settings.json` ya habilita `visualization@melodic-software` — PlantUML render disponible.
- `references/c4-plantuml-usage.md` NO existe — hay que crearlo.
- `discontinued/Prompts/03_generate_component_diagram.md` y `04_generate_container_diagram.md` — referencia conceptual del legacy (C4 Component y Container).

**Lo que NO existe:**
- `workflows/05-component-diagrams.md`
- `prompts/05-component-conceptual.md`
- `prompts/05-component-detailed.md`
- `references/c4-plantuml-usage.md`
- `agents/c4-component-writer.md`
- `agents/diagram-writer.md` → rename a `uml-diagram-writer.md`
- Templates para diagramas C4

**Patrones de M2 relevantes:**
- Workflow → script determinístico → agente semántico → validación humana
- El agente tiene un contrato JSON estricto (nodes_rendered, warnings[], etc.)
- Templates .tpl que el agente rellena con placeholders

### Affected Areas

- `plugins/document-xpp/skills/document-xpp/workflows/05-component-diagrams.md` — NUEVO: workflow principal de Fase 5
- `plugins/document-xpp/skills/document-xpp/prompts/05-component-conceptual.md` — NUEVO: procedimiento Nivel 1
- `plugins/document-xpp/skills/document-xpp/prompts/05-component-detailed.md` — NUEVO: procedimiento Nivel 2
- `plugins/document-xpp/skills/document-xpp/references/c4-plantuml-usage.md` — NUEVO: sintaxis C4-PlantUML stdlib
- `plugins/document-xpp/skills/document-xpp/templates/component-diagram-l1.puml.tpl` — NUEVO: skeleton Nivel 1
- `plugins/document-xpp/skills/document-xpp/templates/component-diagram-l2.puml.tpl` — NUEVO: skeleton Nivel 2
- `plugins/document-xpp/agents/c4-component-writer.md` — NUEVO: agente especializado C4
- `plugins/document-xpp/agents/diagram-writer.md` → `agents/uml-diagram-writer.md` — RENAME: nomenclatura consistente con el nuevo agente
- `plugins/document-xpp/skills/document-xpp/SKILL.md` — UPDATE: habilitar Fase 5, corregir referencias a `uml-diagram-writer`
- `plugins/document-xpp/skills/document-xpp/workflows/03-class-diagrams.md` — UPDATE: Paso 8 apunta a Fase 5 correctamente, corregir referencia a `uml-diagram-writer`

### Approaches

1. **Mismo patrón M2 con script determinístico nuevo** — script Python que genera `component_candidates/<slug>.yaml` para cada grupo antes del agente
   - Pros: arquitectura 100% consistente con M2, determinismo explícito, fácil auditar
   - Cons: overhead — el "candidato" de componentes es trivial (lista de grupos + relaciones); los diagram_candidates YAML ya contienen esa info
   - Effort: High

2. **Workflow directo sin script intermedio — agente lee YAMLs existentes** — el workflow pasa los funcionalidades/*.yaml + diagram_candidates/*.yaml directamente al agente
   - Pros: simple, sin artefactos intermedios adicionales, reutiliza lo que M2 ya generó
   - Cons: el agente tiene más carga de síntesis; si el workflow 03 no corrió (no hay diagram_candidates), el workflow 05 tiene que manejar ese caso
   - Effort: Medium

3. **Workflow con script liviano de síntesis cross-grupo** — un script Python minimal que "aplana" todos los diagram_candidates/*.yaml en un único mapa de componentes con sus relaciones (sin yaml adicional por grupo, sino un único component_map.yaml para el módulo)
   - Pros: el agente Nivel 1 recibe un input ultra-compacto; separación clara determinístico/semántico
   - Cons: otro script a mantener; el mapa de componentes puede quedar desactualizado si no se regenera
   - Effort: Medium-High

### Recommendation

**Opción 2 — Workflow directo sin script intermedio.**

Razón: los `diagram_candidates/<slug>.yaml` ya contienen `external_refs[].{in_inventory, other_group_slug}` que representan exactamente las relaciones cross-grupo. Generar un script adicional para "re-indexar" lo que ya existe en esos YAMLs es redundancia innecesaria.

El workflow 05 sigue la misma estructura que 03 (prerrequisitos, alcance parcial, delegación a agente, validación humana, actualización tracking), con dos diferencias:
1. No necesita un script previo — los inputs son los funcionalidades/*.yaml + diagram_candidates/*.yaml existentes.
2. El agente opera en dos modos: Nivel 1 (agrega todos los grupos en un único .puml) y Nivel 2 (uno por grupo).

**Sobre el skill `anthropic-skills:c4-plantuml`:** el settings.json solo tiene `visualization@melodic-software`. No hay evidencia de que `anthropic-skills:c4-plantuml` esté instalado. Para no crear una dependencia frágil, M3 usa directamente la librería `plantuml-stdlib/C4-PlantUML` via `!include`. Esto hace el plugin self-contained. La referencia `c4-plantuml-usage.md` documenta los macros clave.

**Nuevo agente `component-writer`:** es un agente separado a `diagram-writer` porque la semántica C4 es distinta (macros `Component/Rel` vs sintaxis UML de clases). Reutilizar `diagram-writer` para C4 requeriría overloading que haría el agente inmantenible.

### Risks

- Sin script determinístico, si diagram_candidates no fueron generados (workflow 03 no corrió), el agente Nivel 1 no tiene los `external_refs` con `in_inventory`. Mitigación: el workflow 05 verifica la existencia de diagram_candidates antes de avanzar y, si no existen, corre el script build_class_diagrams.py primero (prerequisito documental, ya contemplado en tracking-schema).
- El Nivel 2 (detallado por grupo) puede solaparse visualmente con el diagrama de clases si el grupo es pequeño (< 5 clases). Mitigación: el prompt indica explícitamente que se agrupan por cluster semántico (Servicios, Contratos, Tablas, Http) sin exponer clases individuales — el nivel de abstracción es distinto.
- `anthropic-skills:c4-plantuml` no está habilitado en settings.json. Mitigación: usar plantuml-stdlib directamente, sin dependencia del skill externo.

### Ready for Proposal

Sí. El scope está bien delimitado, los archivos afectados son claros, y la decisión de arquitectura (sin script intermedio) está justificada con evidencia del codebase.
