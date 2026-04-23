# Proposal: M5 — Modos Incrementales

## Intent

Completar el soporte end-to-end de los modos `actualizar`, `agregar-independiente` y `agregar-relacionado` del plugin `document-xpp`. M1-M4 implementaron todas las fases en modo `nuevo`; M5 cierra el ciclo de vida iterativo del workspace.

## Problem

Los 4 bugs/gaps que bloquean el uso real de los modos incrementales:

1. **Bug: re-clasificación de grupos existentes en `agregar-*`** — el `functional-classifier` recibe el `inventory.csv` completo en modos `agregar-*`, causando que proponga re-agrupar clases ya clasificadas en lugar de enfocarse sólo en las nuevas.

2. **Gap: archivos eliminados no se limpian** — cuando un `.xpp` desaparece de `XppSource`, el diff de hashes lo detecta como `eliminado` pero nadie lo remueve de `classes[]` en el YAML de la funcionalidad. La funcionalidad queda `desactualizado` con una clase fantasma.

3. **Gap: `agregar-relacionado` no actualiza cross-refs** — al agregar un grupo con dependencias en grupos existentes, `build_class_diagrams.py` no se re-corre sobre los grupos existentes, por lo que sus `external_refs` en `diagram_candidates/` no reflejan la nueva relación. El diagrama C4 L1 queda desactualizado.

4. **Gap: `functional_map.md` sobrescrito en modo incremental** — en modo no-`nuevo`, el Paso 6.2 de Workflow 02 sobreescribe el `functional_map.md` completo, perdiendo los links a diagramas (`.puml`) que las fases 3-5 habían agregado para grupos no modificados.

## Approach

Correcciones quirúrgicas en los dos archivos centrales del flujo incremental:

1. **`workflows/02-functional-map.md`** — 4 cambios:
   - Paso 2: cuando `eliminados` no está vacío, limpiar las clases del YAML correspondiente antes de marcar `desactualizado`.
   - Paso 3: en modo `agregar-*`, pre-filtrar el inventory para pasarle al classifier sólo las clases nuevas (huérfanas del Paso 2) + contexto de grupos existentes.
   - Paso 3 (post-`agregar-relacionado`): re-correr `build_class_diagrams.py` sobre grupos existentes afectados para actualizar `external_refs`.
   - Paso 6.2: en modo no-`nuevo`, hacer un merge selectivo del `functional_map.md` — actualizar/agregar sólo los grupos procesados, preservar las secciones de los demás.

2. **`agents/functional-classifier.md`** — 1 cambio:
   - Paso 3: separar explícitamente el comportamiento por modo (`actualizar` = realinear stale groups; `agregar-independiente` = clasificar sólo nuevas clases; `agregar-relacionado` = clasificar nuevas clases + identificar vínculos con grupos existentes).

## Scope

### Modified Capabilities
- `incremental-workflow`: workflow 02 completo para modos no-`nuevo`
- `functional-classifier-agent`: comportamiento diferenciado por modo en `agregar-*`

### New Capabilities
- ninguna (M5 es puro bug-fix y gap-completion sobre lo ya existente)

## Out of Scope

- Soporte incremental en workflows 03/04/05 — ya tienen la lógica de "alcance parcial" por `status` implementada. M5 sólo arregla el upstream (workflow 02).
- Cambios al schema de tracking (`tracking-schema.md`) — no se agregan campos nuevos.
- Migración de workspaces existentes creados con M1-M4.

## Key Decisions

### Solo tocar workflow 02 y functional-classifier

Los workflows 03/04/05 ya tienen la lógica de "sólo regenerar grupos `desactualizado`/`nueva`". El problema real está upstream: un YAML puede tener clases fantasma (eliminadas) o el mapa puede perder links. Corregir el upstream es suficiente.

### Merge selectivo de functional_map.md (no reescritura completa)

En modo incremental, el workflow leerá el `functional_map.md` existente, identificará las secciones de los grupos procesados, las reemplazará, y dejará intactas las de los grupos no tocados (que incluyen los links a `.puml` de Fases 3-5). Esto preserva el trabajo acumulado de sesiones anteriores.

### Pre-filtrado en classifier vs post-filtrado

Mejor pre-filtrar antes de invocar al agente (pasarle sólo las clases nuevas) que dejarle filtrar al agente con instrucciones. El agente trabaja con tokens limitados; darle el inventario completo para que ignore la mayoría es ineficiente y propenso a errores.

## Affected Files

| Archivo | Acción |
|---|---|
| `skills/document-xpp/workflows/02-functional-map.md` | Modificar — 4 puntos clave |
| `plugins/document-xpp/agents/functional-classifier.md` | Modificar — Paso 3 diferenciado por modo |
| `CLAUDE.md` | Modificar — estado M5 |

## Risks

- El merge selectivo de `functional_map.md` es la parte más delicada — si el formato del archivo diverge de lo esperado (el usuario editó el mapa manualmente), el merge puede fallar. Mitigación: si el parsing falla, hacer backup + reescritura completa con warning.
