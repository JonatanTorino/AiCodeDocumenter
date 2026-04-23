# component-diagrams-c4 Specification

## Purpose

Generación de diagramas de componentes C4 en dos niveles de abstracción para un workspace de `document-xpp`: Nivel 1 (módulo completo, un componente por grupo funcional) y Nivel 2 (sub-componentes semánticos por grupo, sin bajar a clases individuales).

---

## Requirements

### Requirement: Prerequisite Check

El workflow MUST verificar que `_tracking/diagram_candidates/` contiene al menos un YAML antes de avanzar. Si no existen, MUST ejecutar `build_class_diagrams.py` primero y abortar si falla.

#### Scenario: diagram_candidates presentes

- GIVEN un workspace con Fases 1–3 completadas y `diagram_candidates/*.yaml` existentes
- WHEN el usuario ejecuta la Fase 5
- THEN el workflow avanza sin correr `build_class_diagrams.py`

#### Scenario: diagram_candidates ausentes

- GIVEN un workspace con Fases 1–2 completadas pero sin `diagram_candidates/`
- WHEN el usuario ejecuta la Fase 5
- THEN el workflow corre `build_class_diagrams.py` antes de continuar
- AND aborta con mensaje claro si el script falla

---

### Requirement: Level 1 Conceptual Diagram

El agente `c4-component-writer` MUST generar un único `diagrams/components/conceptual.puml` donde cada grupo funcional se representa como un `Component` C4. Las relaciones entre grupos MUST derivarse de `external_refs[].{in_inventory: true, other_group_slug}` en los `diagram_candidates/*.yaml`. La sintaxis MUST usar `plantuml-stdlib/C4-PlantUML` (no `anthropic-skills:c4-plantuml`).

#### Scenario: módulo con múltiples grupos relacionados

- GIVEN funcionalidades/*.yaml con N grupos y diagram_candidates con cross-references
- WHEN el agente genera el Nivel 1
- THEN el .puml contiene exactamente N `Component(...)` (uno por grupo)
- AND cada relación cross-grupo detectada en `external_refs[].in_inventory=true` aparece como `Rel(...)`

#### Scenario: grupo sin relaciones externas al módulo

- GIVEN un grupo funcional cuyos `external_refs` tienen `in_inventory: false` únicamente
- WHEN el agente genera el Nivel 1
- THEN el componente del grupo aparece sin aristas salientes hacia otros componentes del módulo

#### Scenario: diagram_candidates sin external_refs in_inventory

- GIVEN todos los grupos sin referencias cross-grupo
- WHEN el agente genera el Nivel 1
- THEN el .puml se genera con N componentes aislados
- AND el agente agrega un `warnings[]` indicando ausencia de relaciones inter-grupo

---

### Requirement: Level 2 Detailed Diagram

El agente MUST generar un `diagrams/components/<slug>/detailed.puml` por cada grupo con `status` en `{nueva, desactualizado}` (o todos en modo `nuevo`). El diagrama MUST agrupar las clases del grupo en clusters semánticos (`Servicios`, `Contratos`, `Tablas`, `Http`, etc.) SIN exponer clases individuales como elementos del diagrama.

#### Scenario: grupo con clases de roles mixtos

- GIVEN un grupo con clases de roles service, dto, table
- WHEN el agente genera el Nivel 2
- THEN el .puml tiene sub-componentes "Servicios", "Contratos" y "Tablas"
- AND ninguna clase individual (e.g. `AxnLicSubscriptionService`) aparece como elemento propio

#### Scenario: grupo con < 5 clases (riesgo de redundancia)

- GIVEN un grupo con menos de 5 clases
- WHEN el agente genera el Nivel 2
- THEN el agente incluye un `warnings[]` sugiriendo que el grupo puede ser demasiado fino para un Nivel 2 significativo

---

### Requirement: Tracking Update

El workflow MUST actualizar `_tracking/funcionalidades/<slug>.yaml` por cada grupo procesado:
- `artifacts.component_diagrams.level_1_node_in` = `"diagrams/components/conceptual.puml"`
- `artifacts.component_diagrams.level_2` = `"diagrams/components/<slug>/detailed.puml"`

#### Scenario: primera generación

- GIVEN `artifacts.component_diagrams.level_1_node_in` vacío
- WHEN el workflow completa ambos niveles para el grupo
- THEN ambos campos quedan populados con sus paths relativos al workspace

---

### Requirement: Human Validation

El workflow MUST presentar cada `.puml` generado al usuario vía `AskUserQuestion` con la opción de Aceptar, Ajustar o Rehacer antes de actualizar el tracking.

#### Scenario: usuario acepta el diagrama

- GIVEN el agente generó un .puml sin warnings críticos
- WHEN el usuario elige "Aceptar"
- THEN el workflow actualiza el tracking y avanza al siguiente grupo

#### Scenario: usuario pide ajuste

- GIVEN el usuario describe una corrección específica
- WHEN elige "Ajustar"
- THEN el workflow reinvoca el agente con las instrucciones adicionales como override
