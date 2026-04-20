# M0.2 — Resultado de la investigación

> **Fecha:** 2026-04-20
> **Método:** inspección vía `WebFetch` de los candidatos del plan + `WebSearch` ampliado a la comunidad.

---

## 1. Candidatos identificados

### 1.1. Del marketplace del plan original (`melodic-software/claude-code-plugins`)

El marketplace expone **40 plugins** (no 35 como decía el plan — ya creció). Los relevantes para UML/diagramas:

| Plugin | Descripción | Skills expuestas |
|--------|-------------|------------------|
| `visualization` | Mermaid + PlantUML, diagrams-as-code | `mermaid-syntax`, `plantuml-syntax`, `diagram-patterns` |
| `formal-specification` | UML/SysML, TLA+, OpenAPI/AsyncAPI, state machines | UML modeling + 7 skills más; agents `specification-architect` y `api-designer`; commands `/specify`, `/api-contract`, `/state-diagram` |
| `documentation-standards` | arc42, C4 model, ADR, RFC, runbooks | `c4-documentation` + command `/doc-architecture format=c4` |

### 1.2. Descubrimientos comunitarios (fuera del plan original)

| Repo | Descripción | Licencia | Observaciones |
|------|-------------|----------|---------------|
| `bitsmuggler/c4-skill` | Skill dedicado a C4: Context/Container/Component/Deployment/Dynamic; scanea codebase | No declarada | Genera **Structurizr DSL**, exporta a PlantUML como paso secundario |
| `SpillwaveSolutions/plantuml` | Cubre los 19 tipos de PlantUML, renderiza a PNG/SVG | No declarada | Requiere **Java JRE + plantuml.jar** (fricción de setup) |
| `jovd83/PlantUML-skill` | PlantUML + C4 en un skill; aesthetic moderno | MIT | Un solo skill monolítico |
| `infobip/plantuml-mcp-server` | Servidor MCP | MIT | Es un MCP, no un skill — fuera de scope |

---

## 2. Matriz de evaluación contra criterios de 3.2 del plan

| Criterio | `visualization` | `formal-specification` | `documentation-standards` | `bitsmuggler/c4-skill` | `SpillwaveSolutions/plantuml` | `jovd83/PlantUML-skill` |
|----------|:---------------:|:----------------------:|:-------------------------:|:----------------------:|:-----------------------------:|:-----------------------:|
| PlantUML clases | ✅ | ⚠️ (UML genérico) | ❌ | ❌ | ✅ | ✅ |
| PlantUML secuencia | ✅ | ❌ | ❌ | ⚠️ (Dynamic) | ✅ | ✅ |
| C4 Component/Container | ✅ | ⚠️ | ✅ | ✅ (especializado) | ⚠️ | ✅ |
| Licencia permisiva | ✅ MIT | ✅ MIT (del marketplace) | ✅ MIT (del marketplace) | ❓ | ❓ | ✅ MIT |
| Mantenimiento/recencia | ✅ | ✅ | ✅ | ⚠️ 10 commits | ⚠️ | ⚠️ 15 commits |
| Dependencias runtime | ✅ ninguna | ✅ ninguna | ✅ ninguna | ❌ Structurizr | ❌ Java+plantuml.jar | ✅ ninguna |
| **Score** | **6/6** | **2.5/6** | **3/6** | **2.5/6** | **3/6** | **5/6** |

**Regla de calificación del plan:** "3 de 4 → B-prime". Los que califican: `visualization`, `jovd83/PlantUML-skill`, `documentation-standards` (parcial).

---

## 3. Hallazgos clave

1. **El plan v3 usaba nombre incorrecto** (`uml-modeling`). El plugin real con mejor fit es `visualization`.
2. **`formal-specification` NO es buen fit**: su foco es TLA+/OpenAPI/SysML, no PlantUML puro. No cubre secuencia ni clases de la forma que necesita `document-xpp`.
3. **`visualization` es el único del marketplace melodic que expone una skill llamada `plantuml-syntax`** como primera ciudadana — exactamente lo que necesita `document-xpp` para apoyarse en sintaxis sin reinventarla.
4. **Skills externas especializadas (bitsmuggler, SpillwaveSolutions) cargan dependencias runtime** (Structurizr, Java) que no aporta valor en este flujo — `document-xpp` solo necesita generar `.puml`, el renderizado queda a cargo del usuario.
5. **Opción C (copiar contenido) queda descartada**: `visualization` cumple, no hace falta.

---

## 4. Fuentes consultadas

- https://github.com/melodic-software/claude-code-plugins/blob/main/.claude-plugin/marketplace.json
- https://github.com/melodic-software/claude-code-plugins/tree/main/plugins/formal-specification
- https://github.com/melodic-software/claude-code-plugins/tree/main/plugins/visualization
- https://github.com/melodic-software/claude-code-plugins/tree/main/plugins/documentation-standards
- https://github.com/bitsmuggler/c4-skill
- https://github.com/SpillwaveSolutions/plantuml
- https://github.com/jovd83/PlantUML-skill
- https://code.claude.com/docs/en/skills
