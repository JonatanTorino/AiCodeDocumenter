# Design: M4 — Diagramas de Secuencia

## Technical Approach

Agregar Fase 4 al plugin con un agente nuevo `sequence-diagram-writer` invocado en dos modos por el workflow 04: primero en modo `discover` (lee `.xpp` → propone flujos candidatos, sin escribir archivos), luego en modo `generate` (genera el `.puml` para un flujo elegido). El workflow orquesta la selección interactiva entre ambas invocaciones.

---

## Architecture Decisions

### Decision: Two-mode agent (discover + generate)

**Choice**: Un único agente `sequence-diagram-writer` con parámetro `mode: "discover" | "generate"`.
**Alternatives considered**: (a) Dos agentes separados. (b) Agente único que genera todo sin selección interactiva.
**Rationale**: La interactividad de la selección fuerza separar discovery de generation. Un solo agente con dos modos evita duplicar la lógica de lectura de `.xpp` y el contrato JSON. Las alternativas son redundantes o rompen el flujo interactivo.

### Decision: sequence-diagram-writer separado de uml-diagram-writer

**Choice**: Nuevo agente `agents/sequence-diagram-writer.md`.
**Alternatives considered**: Extender `uml-diagram-writer` con `diagram_type: "sequence"`.
**Rationale**: `uml-diagram-writer` recibe `candidate_yaml_path` (candidatos precomputados) y `dbml_path` — ninguno aplica a secuencias. Agregar condicionales lo convertiría en un agente God. La separación es coherente con la decisión de M3 (se creó `c4-component-writer` separado).

### Decision: xpp_root se obtiene del manifest

**Choice**: El workflow lee `_tracking/manifest.yaml` para obtener `xpp_root` y lo pasa al agente.
**Alternatives considered**: El agente busca `xpp_root` en el funcionalidad YAML o lo recibe como input directo del usuario.
**Rationale**: `manifest.yaml` es la fuente de verdad del workspace (lo estableció Fase 1). Los archivos de funcionalidad no lo repiten para evitar duplicación.

---

## Data Flow

```
Workflow 04
  │
  ├─ 1. Leer funcionalidades/*.yaml → listar grupos
  ├─ 2. Leer manifest.yaml → obtener xpp_root
  │
  ├─ 3. Agent: sequence-diagram-writer (mode=discover)
  │      ├─ Input: funcionalidad_yaml_path, xpp_root
  │      └─ Output JSON: { candidates: [{name, entry_point, participants[]}] }
  │
  ├─ 4. AskUserQuestion → usuario elige flujos
  │
  └─ 5. Por cada flujo elegido:
         ├─ Agent: sequence-diagram-writer (mode=generate)
         │      ├─ Input: funcionalidad_yaml_path, xpp_root, flow_name, entry_point, puml_output_path
         │      └─ Output JSON + escribe .puml en disco
         │
         ├─ 6. AskUserQuestion → Aceptar / Ajustar / Rehacer
         └─ 7. Actualizar funcionalidades/<slug>.yaml
```

---

## File Changes

| Archivo | Acción | Descripción |
|---|---|---|
| `agents/sequence-diagram-writer.md` | Crear | Agente dos modos: discover (propone candidatos) + generate (escribe .puml) |
| `skills/document-xpp/workflows/04-sequence-diagrams.md` | Crear | Orquestador interactivo Fase 4 |
| `skills/document-xpp/prompts/04-sequence-diagram.md` | Crear | Procedimiento paso a paso para el agente |
| `skills/document-xpp/templates/sequence-diagram.puml.tpl` | Crear | Skeleton PlantUML: !theme plain, autonumber, 3 boxes, placeholders |
| `skills/document-xpp/references/visual-conventions.md` | Modificar | Agregar sección `## Sequence Diagrams` al final |
| `skills/document-xpp/SKILL.md` | Modificar | Fila Fase 4: quitar "no disponible todavía", actualizar descripción |
| `skills/document-xpp/workflows/03-class-diagrams.md` | Modificar | Paso final: next-phase apunta a `04-sequence-diagrams.md` |
| `CLAUDE.md` | Modificar | Estado actual: M4 en progreso / mergeado |

---

## Interfaces / Contracts

### Agent inputs (ambos modos)

```yaml
mode: discover | generate
funcionalidad_yaml_path: "<abs-path>/_tracking/funcionalidades/<slug>.yaml"
xpp_root: "<abs-path>/XppSource/"
workspace_path: "<abs-path>/"
template_path: "<plugin-root>/templates/sequence-diagram.puml.tpl"
prompt_path: "<plugin-root>/prompts/04-sequence-diagram.md"
visual_conventions_path: "<plugin-root>/references/visual-conventions.md"
# Solo en mode=generate:
flow_name: "Crear Suscripción"
entry_point: "AxnLicSubscriptionController"
puml_output_path: "<workspace>/diagrams/sequences/<slug>-<flow-slug>.puml"
```

### Agent output — mode: discover

```json
{
  "group_slug": "subscription",
  "candidates": [
    {
      "name": "Crear Suscripción",
      "entry_point": "AxnLicSubscriptionController",
      "participants": ["AxnLicSubscriptionController", "AxnLicSubscriptionService", "AxnLicSubscription"]
    }
  ],
  "warnings": []
}
```

### Agent output — mode: generate

```json
{
  "group_slug": "subscription",
  "flow_name": "Crear Suscripción",
  "flow_slug": "crear-suscripcion",
  "puml_path": "C:/.../diagrams/sequences/subscription-crear-suscripcion.puml",
  "participants_rendered": 4,
  "external_participants": ["SysOperationController"],
  "warnings": []
}
```

### flow-slug derivation

El workflow normaliza `flow_name` a kebab-case ASCII para construir el path:
- Minúsculas, tildes → equivalente ASCII (`ó` → `o`, `ú` → `u`, `ñ` → `n`)
- Espacios → `-`
- Ejemplo: `"Crear Suscripción"` → `crear-suscripcion`

### Tracking update

```yaml
artifacts:
  sequence_diagrams:
    - name: "Crear Suscripción"
      file: diagrams/sequences/subscription-crear-suscripcion.puml
```

---

## Visual Conventions — Sequence Section (new)

Agregar al final de `visual-conventions.md`:

```
## Sequence Diagrams

### 3-layer structure (obligatoria)
- box "Presentation": AxForm, actor usuario, menus
- box "Business Logic": AxClass — Services, Controllers, Managers
- box "Data": AxTable, Queries

### Colores por capa
skinparam participant {
  BackgroundColor<<Form>>     #F3E5F5
  BorderColor<<Form>>         #7B1FA2
  BackgroundColor<<Table>>    #E8F5E9
  BorderColor<<Table>>        #2E7D32
  BackgroundColor<<External>> #ECEFF1
  BorderColor<<External>>     #B0BEC5
}

### Reglas de ruido (obligatorias)
- NO incluir: parm*(), new() triviales, validaciones internas sin lógica de negocio
- SÍ incluir: validate(), run(), post(), calc(), update(), métodos de persistencia

### Otros (obligatorios)
- autonumber siempre
- activate/deactivate en participantes principales
- <<External>> para clases fuera del inventory.csv
- title con nombre del flujo de negocio
```

---

## Testing Strategy

| Layer | Qué verificar | Cómo |
|---|---|---|
| Static | Grep `"no disponible todavía"` en SKILL.md — debe dar 0 resultados | Bash grep |
| Static | `04-sequence-diagrams.md` existe y tiene los 7 pasos | Read |
| Static | Template `sequence-diagram.puml.tpl` tiene `autonumber`, 3 boxes, `title` | Read + grep |
| Manual | Workflow 04 contra `.validation/` con workspace real Fases 1-3 completas | Manual |

---

## Migration / Rollout

No migration required. Los `funcionalidades/*.yaml` existentes no tienen `artifacts.sequence_diagrams` — el campo se agrega la primera vez que se corre Fase 4 sobre ese grupo. YAML es aditivo.

## Open Questions

- Ninguna.
