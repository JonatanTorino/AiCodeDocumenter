# Design: M3 — Diagramas de Componentes C4

## Technical Approach

Workflow `05-component-diagrams.md` lee YAMLs existentes de M2 (sin script intermedio) y delega al agente `c4-component-writer` en dos invocaciones: Nivel 1 (todos los grupos → `conceptual.puml`) y Nivel 2 (por grupo → `<slug>/detailed.puml`). El rename de `diagram-writer` → `uml-diagram-writer` es parte del mismo PR para mantener coherencia de nomenclatura.

---

## Architecture Decisions

| Decisión | Elegido | Rechazado | Razón |
|----------|---------|-----------|-------|
| Input al agente | YAMLs existentes de M2 | Nuevo script Python | `external_refs[].in_inventory` ya contiene las relaciones cross-grupo; script sería re-indexar lo mismo |
| Agente | Nuevo `c4-component-writer` | Extender `uml-diagram-writer` | Semántica C4 (`Component/Rel`) ≠ UML (`class/-->`); mezclar requiere condicionales que degradan mantenibilidad |
| Sintaxis C4 | `plantuml-stdlib/C4-PlantUML` (`!include <C4/C4_Component.puml>`) | `anthropic-skills:c4-plantuml` | No habilitado en `.claude/settings.json`; evitar dependencia frágil |
| Rename agente M2 | `diagram-writer` → `uml-diagram-writer` en mismo PR | Dejar nombre viejo | Con prefijo de tecnología en ambos agentes, el nombre viejo queda ambiguo |

---

## Data Flow

```
Fase 5 — Nivel 1
funcionalidades/*.yaml  ──┐
                           ├──→ c4-component-writer ──→ diagrams/components/conceptual.puml
diagram_candidates/*.yaml ─┘       (L1 mode)

Fase 5 — Nivel 2 (por grupo)
funcionalidades/<slug>.yaml  ──┐
                                ├──→ c4-component-writer ──→ diagrams/components/<slug>/detailed.puml
diagram_candidates/<slug>.yaml ─┘       (L2 mode)
```

**Construcción del mapa cross-grupo (Nivel 1):**
El agente lee `external_refs[]` de cada `diagram_candidates/*.yaml` filtrando `in_inventory: true`. Cada par `(slug_origen, other_group_slug)` se convierte en un `Rel(...)` en el diagrama.

**Clusters semánticos (Nivel 2):**
El agente mapea `nodes[].{role, artifact_kind}` a clusters:

| role / artifact_kind | Cluster |
|---|---|
| `service` | Servicios |
| `controller` | Controladores |
| `dto` | Contratos |
| `table` | Tablas |
| `view` | Vistas |
| `helper` | Utilidades |
| `other` | Utilidades |

Clusters con 0 clases se omiten sin warning.

---

## File Changes

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `agents/diagram-writer.md` | Rename → `uml-diagram-writer.md` | Nomenclatura consistente |
| `agents/c4-component-writer.md` | Create | Agente C4 — persona, inputs, contrato JSON |
| `skills/.../workflows/05-component-diagrams.md` | Create | Orquestación Fase 5 (prerequisito, L1, L2, validación, tracking) |
| `skills/.../prompts/05-component-conceptual.md` | Create | Procedimiento Nivel 1 paso a paso |
| `skills/.../prompts/05-component-detailed.md` | Create | Procedimiento Nivel 2 paso a paso |
| `skills/.../references/c4-plantuml-usage.md` | Create | Referencia sintaxis C4-PlantUML stdlib (macros clave) |
| `skills/.../templates/component-diagram-l1.puml.tpl` | Create | Skeleton Nivel 1 con placeholders Mustache |
| `skills/.../templates/component-diagram-l2.puml.tpl` | Create | Skeleton Nivel 2 con placeholders Mustache |
| `skills/.../SKILL.md` | Modify | Habilitar Fase 5; actualizar ref a `uml-diagram-writer` |
| `skills/.../workflows/03-class-diagrams.md` | Modify | Paso 8 next-phase correcto; actualizar ref a `uml-diagram-writer` |
| `skills/.../prompts/03-class-diagram.md` | Modify | Actualizar ref a `uml-diagram-writer` |
| `skills/.../references/visual-conventions.md` | Modify | 3 refs a `uml-diagram-writer` |
| `skills/.../references/tracking-schema.md` | Modify | 1 ref a `uml-diagram-writer` |
| `skills/.../scripts/build_class_diagrams.py` | Modify | Docstring: 1 ref a `uml-diagram-writer` |
| `README.md` | Modify | Árbol de agentes: `uml-diagram-writer.md` + `c4-component-writer.md` |

---

## Interfaces / Contracts

**Contrato JSON de `c4-component-writer` (output estricto):**

```json
{
  "level": "conceptual",
  "group_slug": "",
  "puml_path": "<workspace>/diagrams/components/conceptual.puml",
  "components_rendered": 7,
  "relations_rendered": 5,
  "omitted_groups": [],
  "warnings": []
}
```

```json
{
  "level": "detailed",
  "group_slug": "subscription",
  "puml_path": "<workspace>/diagrams/components/subscription/detailed.puml",
  "components_rendered": 3,
  "relations_rendered": 2,
  "omitted_groups": [],
  "warnings": ["grupo con < 5 clases — Nivel 2 puede ser redundante con el diagrama de clases"]
}
```

**Inputs que el workflow pasa al agente:**
- `funcionalidades_dir` — `_tracking/funcionalidades/` (L1) o `_tracking/funcionalidades/<slug>.yaml` (L2)
- `candidates_dir` — `_tracking/diagram_candidates/` (L1) o `_tracking/diagram_candidates/<slug>.yaml` (L2)
- `puml_output_path` — path absoluto del `.puml` a escribir
- `template_path` — path al `.tpl` correspondiente (L1 o L2)
- `prompt_path` — path al `prompts/05-component-conceptual.md` o `05-component-detailed.md`
- `workspace_path` — raíz del workspace

---

## Testing Strategy

| Layer | Qué validar | Approach |
|-------|-------------|----------|
| Manual E2E | Workflow 05 end-to-end sobre workspace golden | Correr contra `.validation/` sample; verificar render en VS Code |
| Manual L1 | `conceptual.puml` tiene N componentes y M relaciones correctas | Inspección visual post-generación |
| Manual L2 | `detailed.puml` agrupa por clusters, sin clases individuales | Inspección visual + grep `class ` en .puml (no debe aparecer) |
| Rename | Ningún archivo en `plugins/` contiene `diagram-writer` post-PR | `grep -r "diagram-writer" plugins/` debe devolver 0 resultados |

---

## Migration / Rollout

El rename afecta 9 archivos existentes. El workflow 05 es Fase 5 — sólo se activa si el usuario la invoca explícitamente. No hay migración de datos de workspace (el tracking schema ya tiene los campos `component_diagrams.*` vacíos desde M2).

## Open Questions

- Ninguna. El scope está completamente definido.
