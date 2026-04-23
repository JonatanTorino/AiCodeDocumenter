# Sequence Diagrams Specification

## Purpose

Fase 4 del plugin `document-xpp`. Genera diagramas UML de secuencia (`diagrams/sequences/<slug>-<flow-slug>.puml`) a partir del código X++ de un grupo funcional, con flujo interactivo: el agente propone flujos candidatos y el usuario decide cuáles diagramar.

---

## Requirements

### Requirement: Prerequisite Check

El workflow Fase 4 MUST verificar que el workspace tiene al menos un `_tracking/funcionalidades/<slug>.yaml` con `status: actualizado` o `status: nueva` antes de avanzar. Si no hay funcionalidades procesadas, MUST detener el flujo con mensaje explícito indicando que Fases 1 y 2 deben completarse primero.

#### Scenario: workspace sin funcionalidades

- GIVEN que el workspace no tiene archivos en `_tracking/funcionalidades/`
- WHEN el usuario invoca Fase 4
- THEN el workflow detiene el flujo con mensaje `"Fase 4 requiere funcionalidades documentadas. Corré primero Fases 1 y 2."`
- AND no invoca ningún agente

#### Scenario: workspace con funcionalidades disponibles

- GIVEN que existen `_tracking/funcionalidades/*.yaml` con al menos una entrada
- WHEN el usuario invoca Fase 4
- THEN el workflow lista los grupos disponibles y pregunta cuál documentar

---

### Requirement: Candidate Flow Discovery

El agente `sequence-diagram-writer` MUST leer los archivos `.xpp` del grupo funcional e identificar flujos candidatos. Un flujo candidato es una operación de negocio identificable por un usuario final (p.ej.: "Crear suscripción", "Validar licencia"), NOT un método técnico aislado (p.ej.: un getter, un constructor trivial).

Un flujo candidato MUST tener:
- Un entry point claro (método de `Controller`, `Service` o `Form`)
- Al menos 2 participantes en la llamada (actor + un objeto del sistema)

#### Scenario: identificación de flujos en grupo con Controller

- GIVEN un grupo funcional con clases `.xpp` clasificadas
- WHEN el agente lee los archivos X++ del grupo
- THEN produce una lista de flujos candidatos con nombre de negocio (no nombre técnico del método)
- AND cada candidato incluye el entry point y los participantes detectados

#### Scenario: grupo sin entry points identificables

- GIVEN un grupo con sólo helpers o DTOs (sin Controller ni Service con métodos de negocio)
- WHEN el agente lee los archivos X++
- THEN produce lista vacía de candidatos
- AND el workflow informa al usuario con `AskUserQuestion` ofreciendo la posibilidad de describir el flujo manualmente

---

### Requirement: Interactive Flow Selection

El workflow MUST presentar los flujos candidatos al usuario con `AskUserQuestion` antes de generar cualquier diagrama. El usuario MUST poder seleccionar un subconjunto o todos.

#### Scenario: usuario selecciona flujos específicos

- GIVEN que el agente propuso N flujos candidatos
- WHEN el usuario selecciona un subconjunto M ≤ N
- THEN el workflow genera diagramas sólo para los M flujos seleccionados
- AND omite los N-M restantes sin error

#### Scenario: usuario acepta todos los candidatos

- GIVEN que el agente propuso N flujos candidatos
- WHEN el usuario responde "todos" o equivalente
- THEN el workflow genera N diagramas secuencialmente

---

### Requirement: Sequence Diagram Generation

Por cada flujo seleccionado, el agente MUST generar un archivo `.puml` válido en `<workspace>/diagrams/sequences/<slug>-<flow-slug>.puml`.

El diagrama MUST:
- Usar el template `sequence-diagram.puml.tpl`
- Organizar participantes en 3 capas: Presentation, Business Logic, Data
- Aplicar los colores de capa definidos en `visual-conventions.md` (sección Sequence)
- Incluir `autonumber` para trazabilidad
- Omitir getters/setters (`parmXxx`), constructores triviales y validaciones menores sin lógica de negocio
- Representar clases fuera del inventory como participante `<<External>>`

El diagrama SHOULD:
- Incluir `activate`/`deactivate` para los participantes principales
- Agregar `title` con el nombre del flujo de negocio

#### Scenario: generación exitosa de un flujo con 3 capas

- GIVEN flujo "Crear Suscripción" con Form, Service y Table identificados
- WHEN el agente genera el diagrama
- THEN el `.puml` tiene un box "Presentation" con el Form, un box "Business Logic" con el Service, y un box "Data" con la Table
- AND los métodos triviales (parm*, new) no aparecen

#### Scenario: referencia a clase fuera del inventory

- GIVEN que el código X++ llama a `Info()` o `SysOperationController` del framework D365
- WHEN el agente genera el diagrama
- THEN la clase externa aparece como participante `<<External>>`
- AND el flujo termina al alcanzar el external (no se expande)

#### Scenario: diagrama vacío por falta de archivos .xpp

- GIVEN que los archivos `.xpp` del grupo no existen en `xpp_root`
- WHEN el agente intenta generar el diagrama
- THEN NO escribe ningún `.puml`
- AND devuelve JSON con `puml_path: ""` y `warnings` explicando la causa

---

### Requirement: Tracking Update

Por cada diagrama generado, el workflow MUST actualizar `_tracking/funcionalidades/<slug>.yaml`:
- `artifacts.sequence_diagrams[]` MUST incluir `{name: "<nombre del flujo>", file: "diagrams/sequences/<slug>-<flow-slug>.puml"}`
- `last_updated` MUST actualizarse a la fecha/hora actual (ISO-8601 UTC)

#### Scenario: primer diagrama de secuencia para un grupo

- GIVEN que `artifacts.sequence_diagrams` no existe o está vacío en el YAML
- WHEN el workflow genera el primer diagrama
- THEN `artifacts.sequence_diagrams` tiene exactamente 1 entrada
- AND `last_updated` fue actualizado

#### Scenario: segunda corrida agrega sin duplicar

- GIVEN que `artifacts.sequence_diagrams` ya tiene 1 entrada
- WHEN el workflow genera un segundo flujo del mismo grupo
- THEN `artifacts.sequence_diagrams` tiene 2 entradas (la preexistente y la nueva)
- AND no hay entradas duplicadas

---

### Requirement: Human Validation per Diagram

Por cada `.puml` generado, el workflow MUST presentar al usuario un resumen (Grupo, Flujo, Participantes: N, path) con `AskUserQuestion` ofreciendo: Aceptar, Ajustar o Rehacer — igual que Fase 3 y Fase 5.

#### Scenario: usuario acepta el diagrama

- GIVEN que el workflow presentó el resumen de un diagrama
- WHEN el usuario responde "Aceptar"
- THEN el workflow avanza al siguiente flujo pendiente

#### Scenario: usuario solicita ajuste

- GIVEN que el workflow presentó el resumen de un diagrama
- WHEN el usuario describe una corrección
- THEN el workflow reinvoca el agente con las instrucciones adicionales como override en el prompt
