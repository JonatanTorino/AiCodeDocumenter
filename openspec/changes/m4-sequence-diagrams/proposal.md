# Proposal: M4 — Diagramas de Secuencia

## Intent

Habilitar la Fase 4 del plugin `document-xpp`: generación de diagramas de secuencia UML a partir del código X++ de un grupo funcional, con un flujo interactivo donde el agente propone los flujos candidatos y el usuario decide cuáles diagramar.

## Problem

La Fase 4 está referenciada en SKILL.md como "no disponible todavía". El usuario que documenta un módulo D365 F&O hoy no puede generar diagramas de secuencia sin abandonar el plugin y usar el prompt legacy `discontinued/Prompts/05_generate_sequence_diagrams.md` manualmente.

## Approach

Agregar:
1. Un workflow interactivo `04-sequence-diagrams.md` que lee las funcionalidades del workspace, identifica flujos candidatos leyendo el `.xpp`, pregunta al usuario cuáles diagramar, invoca el agente por flujo, y actualiza el tracking.
2. Un nuevo agente `sequence-diagram-writer.md` especializado para secuencias (el `uml-diagram-writer` existente está acoplado a diagramas de clases con candidate YAML + DBML; secuencias no tienen ni candidatos precomputados ni DBML).
3. Un prompt `04-sequence-diagram.md` con el procedimiento paso a paso para el agente.
4. Un template `sequence-diagram.puml.tpl` con el skeleton PlantUML.
5. Una sección de convenciones de secuencia en `visual-conventions.md`.
6. Actualizar SKILL.md (habilitar Fase 4) y CLAUDE.md (estado M4).

## Scope

### New Capabilities
- `sequence-diagrams`: flujo interactivo Workflow 04 + agente sequence-diagram-writer

### Modified Capabilities
- `skill-entry-point`: SKILL.md habilita Fase 4 (quita "no disponible todavía"), actualiza next-phase de Fase 3
- `visual-conventions`: agrega sección de convenciones para diagramas de secuencia

## Out of Scope

- Script determinístico para candidatos de secuencia (Fase 4 es puramente semántica — no hay análisis estático que identifique "flujos" de negocio sin juicio del LLM).
- Soporte multi-flujo en paralelo (los flujos se generan secuencialmente, uno por uno).
- Modo `actualizar` para secuencias (M5).

## Key Decisions

### sequence-diagram-writer separado de uml-diagram-writer

`uml-diagram-writer` recibe `candidate_yaml_path` (candidatos precomputados por `build_class_diagrams.py`), `dbml_path`, y produce un JSON acoplado a diagramas de clases. Para secuencias:
- No hay candidate YAML — el agente lee los `.xpp` directamente y propone flujos
- No se usa DBML (las tablas son participantes, no objetos con columnas)
- El output JSON tiene campos distintos (`flows_rendered`, `participants`, etc.)

Separar los agentes evita un agente God con condicionales `if diagram_type == "class" else ...`.

### Flujo de candidatos: propuesta del agente, no script

Los flujos de negocio requieren comprensión semántica del código. Un script puede listar los entry points (métodos públicos de Controllers/Services) pero no puede inferir cuáles son "flujos de negocio" sin contexto funcional. El agente lee los `.xpp` + los `inputs_registered` opcionales y propone con AskUserQuestion.

### Convenciones: sección nueva en visual-conventions.md

Mantener un único archivo de referencia para todas las convenciones de diagramas. La sección de secuencia define: 3 capas (Presentation / Business Logic / Data), paleta de colores por capa, reglas de ruido (no parmMethods, no new triviales), autonumber obligatorio.

## Affected Files

| Archivo | Acción |
|---|---|
| `agents/sequence-diagram-writer.md` | Crear |
| `skills/document-xpp/workflows/04-sequence-diagrams.md` | Crear |
| `skills/document-xpp/prompts/04-sequence-diagram.md` | Crear |
| `skills/document-xpp/templates/sequence-diagram.puml.tpl` | Crear |
| `skills/document-xpp/references/visual-conventions.md` | Modificar (agregar sección) |
| `skills/document-xpp/SKILL.md` | Modificar (habilitar Fase 4) |
| `skills/document-xpp/workflows/03-class-diagrams.md` | Modificar (next-phase pointer) |
| `CLAUDE.md` | Modificar (estado M4) |

## Risks

- El agente puede proponer flujos demasiado granulares (un método = un flujo). Mitigación: el prompt define que un flujo es un "caso de uso identificable por un usuario de negocio".
- Sin DBML en secuencias: las tablas se representan como participantes sin estructura → aceptable, es la convención de secuencia.
