# Tasks: M5 — Modos Incrementales

## Phase 1: Workflow 02 — Cleanup de eliminados (Paso 2)

- [x] 1.1 En `workflows/02-functional-map.md` Paso 2: agregar bloque de cleanup — para cada archivo en `eliminados`, buscar en todos los YAMLs la clase correspondiente, removerla de `classes[]`, marcar el YAML como `desactualizado`
- [x] 1.2 En el mismo Paso 2: agregar manejo del caso "grupo queda sin clases" — presentar `AskUserQuestion` ofreciendo eliminarlo del tracking

## Phase 2: Workflow 02 — Pre-filtrado de inventory y post-re-run (Paso 3)

- [x] 2.1 En `workflows/02-functional-map.md` Paso 3: agregar bloque condicional para `agregar-*` — construir set de clases asignadas (union de `classes[]` de todos los YAMLs), derivar huérfanas (inventory minus asignadas), pasar solo huérfanas al classifier
- [x] 2.2 En `workflows/02-functional-map.md` Paso 3 (o como Paso 3b): agregar bloque post-aceptación para `agregar-relacionado` — re-correr `build_class_diagrams.py`, comparar `external_refs` antes/después, marcar grupos afectados como stale en `artifacts.component_diagrams`, informar al usuario

## Phase 3: Workflow 02 — Selective merge de functional_map.md (Paso 6.2)

- [x] 3.1 En `workflows/02-functional-map.md` Paso 6.2: reemplazar instrucción de sobreescritura completa por algoritmo de merge selectivo — parsear secciones `## ` existentes, reemplazar/agregar las de grupos procesados, preservar las demás
- [x] 3.2 En el mismo Paso 6.2: agregar fallback — si el parsing falla, hacer backup como `.bak`, reescribir completo, avisar al usuario con `warning`

## Phase 4: functional-classifier — Diferenciación por modo (Paso 3)

- [x] 4.1 En `agents/functional-classifier.md` Paso 3: expandir con comportamiento explícito por modo — `actualizar` (realinear solo grupos stale, no proponer nuevos), `agregar-independiente` (clasificar solo clases huérfanas pre-filtradas), `agregar-relacionado` (clasificar huérfanas + incluir `related_to[]` en output)
- [x] 4.2 En `agents/functional-classifier.md` sección "Output — contrato JSON": agregar campo opcional `related_to[]` al schema del grupo, con nota de que solo aparece en modo `agregar-relacionado`

## Phase 5: CLAUDE.md

- [x] 5.1 Actualizar `CLAUDE.md` — cambiar estado de M5 a "en desarrollo" con fecha y descripción
