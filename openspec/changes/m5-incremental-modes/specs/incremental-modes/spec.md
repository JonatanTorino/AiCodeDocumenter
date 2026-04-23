# Incremental Modes Specification

## Purpose

Completar el soporte de los modos `actualizar`, `agregar-independiente` y `agregar-relacionado` en el plugin `document-xpp`. Las specs de esta sección describen los comportamientos que M5 agrega o corrige sobre la implementación existente de Workflow 02 y el agente `functional-classifier`.

---

## Requirements

### Requirement: Deleted Files Cleanup

Cuando el diff de hashes detecta archivos `eliminados` (presentes en `hashes.previous.csv`, ausentes en `hashes.csv`), el workflow MUST remover esas clases de `classes[]` en los YAMLs de funcionalidades correspondientes antes de marcar el grupo como `desactualizado`.

Si tras la limpieza `classes[]` queda vacío, el workflow MUST incluir un warning al usuario indicando que el grupo quedó sin clases y preguntar si debe eliminarse.

#### Scenario: archivo .xpp eliminado de XppSource

- GIVEN modo `actualizar` con `hashes.previous.csv` existente
- WHEN el diff detecta un archivo en `eliminados`
- THEN el workflow identifica la funcionalidad que tenía esa clase en `classes[]`
- AND la remueve del array
- AND marca la funcionalidad como `status: desactualizado`

#### Scenario: grupo queda sin clases tras eliminación

- GIVEN que después de remover la clase eliminada, `classes[]` queda vacío
- WHEN el workflow termina la limpieza
- THEN presenta un `AskUserQuestion` al usuario: "El grupo `<slug>` quedó sin clases. ¿Lo elimino del tracking?"
- AND si el usuario confirma, elimina el YAML y remueve el grupo del `functional_map.md`

---

### Requirement: Pre-filtered Inventory for agregar-* Modes

En modos `agregar-independiente` y `agregar-relacionado`, el workflow MUST pre-filtrar el `inventory.csv` antes de invocar al `functional-classifier`, pasándole sólo las clases que NO pertenecen a ninguna funcionalidad existente (huérfanas).

El classifier NO debe recibir el inventario completo en estos modos, para evitar que re-proponga grupos ya clasificados.

#### Scenario: agregar-independiente con clases nuevas

- GIVEN modo `agregar-independiente`
- WHEN el workflow prepara los inputs del classifier
- THEN pasa sólo las clases huérfanas (detectadas como `nuevos` en el diff de hashes o no asignadas en ningún YAML)
- AND pasa `existing_functionalities` como contexto de referencia (slugs + names)
- AND el classifier devuelve grupos SÓLO para las clases huérfanas

#### Scenario: classifier no re-propone grupos existentes

- GIVEN modo `agregar-independiente` con 5 clases nuevas y 30 clases ya clasificadas
- WHEN el classifier recibe los inputs
- THEN la propuesta JSON contiene sólo grupos derivados de las 5 clases nuevas
- AND ningún grupo existente aparece en la propuesta

---

### Requirement: agregar-relacionado Cross-group Update

En modo `agregar-relacionado`, una vez que el usuario acepta la propuesta de nuevo grupo, el workflow MUST re-ejecutar `build_class_diagrams.py` sobre todos los grupos del workspace para actualizar `external_refs` en los `diagram_candidates/*.yaml`.

Los grupos cuyos `external_refs` cambien (porque ahora referencian al nuevo grupo) MUST ser marcados con `artifacts.component_diagrams` stale, para que Fase 5 los regenere en la próxima corrida.

#### Scenario: nuevo grupo relacionado agrega external_refs a grupos existentes

- GIVEN modo `agregar-relacionado`, nuevo grupo "Billing" aceptado
- WHEN el workflow re-corre `build_class_diagrams.py`
- THEN los grupos existentes que referencian clases de "Billing" tienen `external_refs` actualizado con `other_group_slug: "billing"` e `in_inventory: true`
- AND esos grupos son informados al usuario como "afectados — sus diagramas C4 necesitan regeneración"

#### Scenario: agregar-relacionado sin impacto en externos

- GIVEN modo `agregar-relacionado`, nuevo grupo aceptado
- WHEN `build_class_diagrams.py` re-corre
- THEN si ningún grupo existente referencia clases del nuevo grupo, no se marcan grupos como stale
- AND el workflow informa "sin impacto en diagramas existentes"

---

### Requirement: Selective functional_map.md Merge

En modos no-`nuevo`, el workflow MUST actualizar `functional_map.md` de forma selectiva: reemplazar las secciones de los grupos procesados en la sesión actual, preservando intactas las secciones de los grupos no modificados (incluyendo sus links a diagramas).

El workflow MUST NOT sobreescribir el archivo completo en modos incrementales.

#### Scenario: actualizar actualiza sólo las secciones afectadas

- GIVEN modo `actualizar`, `functional_map.md` existente con links a `.puml` de todos los grupos
- WHEN el workflow persiste los grupos `desactualizado` regenerados
- THEN sólo las secciones de esos grupos son actualizadas en el mapa
- AND las secciones de los grupos `actualizado` (no procesados) permanecen intactas, con sus links a `.puml`

#### Scenario: agregar-* agrega sección nueva al mapa

- GIVEN modo `agregar-independiente`, nuevo grupo aceptado
- WHEN el workflow persiste el nuevo grupo
- THEN se agrega una nueva sección al `functional_map.md` al final del archivo
- AND las secciones existentes no se modifican

#### Scenario: merge fallback ante formato inesperado

- GIVEN que el usuario editó manualmente `functional_map.md` y su formato no coincide con el esperado
- WHEN el workflow intenta hacer el merge selectivo
- THEN hace backup del archivo como `functional_map.md.bak`
- AND reescribe el archivo completo con todos los grupos actuales
- AND agrega un `warning` al usuario indicando que se hizo reescritura completa y se generó backup

---

### Requirement: functional-classifier Mode Differentiation

El agente `functional-classifier` MUST comportarse de forma diferente según el modo recibido:

- **`nuevo`**: clasificar todo el inventario en grupos desde cero.
- **`actualizar`**: realinear sólo los grupos `desactualizado` con el inventario actualizado. No proponer nuevos grupos a menos que haya clases sin asignar.
- **`agregar-independiente`**: clasificar SÓLO las clases pre-filtradas (huérfanas). Devolver grupos nuevos sin tocar los existentes.
- **`agregar-relacionado`**: clasificar las clases huérfanas Y identificar explícitamente con qué grupos existentes se relacionan, incluyendo `related_to[]` en el output JSON.

#### Scenario: agregar-relacionado identifica vínculos con existentes

- GIVEN modo `agregar-relacionado`, 4 clases nuevas con dependencias en grupo "subscription"
- WHEN el classifier analiza las clases nuevas
- THEN el grupo propuesto incluye `"related_to": ["subscription"]`
- AND el workflow puede usar este campo para marcar el nuevo grupo como candidato a cross-group relationship en los diagram_candidates

#### Scenario: actualizar no propone nuevos grupos innecesarios

- GIVEN modo `actualizar`, 2 clases modificadas en grupo "subscription"
- WHEN el classifier recibe los inputs
- THEN sólo propone ajustes/realineamiento para el grupo "subscription"
- AND NO propone grupos nuevos (las clases ya están asignadas)
