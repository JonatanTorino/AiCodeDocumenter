# Design: M5 — Modos Incrementales

## Technical Approach

4 cambios quirúrgicos en `workflows/02-functional-map.md` + 1 en `agents/functional-classifier.md`. Sin archivos nuevos; todos los cambios son adiciones o reemplazos de secciones existentes.

## Architecture Decisions

### Decision: Deleted Files Cleanup en Paso 2 (no en Paso 6)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Limpiar en Paso 2, antes de invocar al classifier | El classifier nunca ve clases fantasma; el YAML queda limpio antes de cualquier procesamiento | ✅ Elegida |
| Limpiar en Paso 6 al persistir | Más fácil de agrupar con el resto de la persistencia | ❌ El classifier podría ver clases eliminadas y proponer re-clasificación errónea |

**How:** Paso 2 itera `eliminados`. Para cada archivo eliminado, busca en todos los funcionalidades YAMLs cuál tiene esa clase en `classes[]`, la remueve, y marca el YAML como `desactualizado`. Si `classes[]` queda vacío → `AskUserQuestion` preguntando si eliminar el grupo.

---

### Decision: Pre-filter en workflow (no en el agente)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Workflow pre-filtra y pasa solo huérfanas al agente | El agente trabaja con tokens mínimos; no puede re-proponer grupos existentes por error | ✅ Elegida |
| Agente recibe inventory completo + instrucción de ignorar ya-clasificadas | El agente puede equivocarse bajo carga; ineficiente con inventarios grandes | ❌ |

**How:** Antes de invocar al classifier en modos `agregar-*`, el workflow construye el set de clases ya asignadas (leyendo `classes[].file` de todos los YAMLs existentes) y lo resta del `inventory.csv`. Solo las clases que no aparecen en ningún YAML son "huérfanas". Esas son las que pasan al classifier.

---

### Decision: Selective merge por secciones `##` (no por tabla interna)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Parsear por encabezados `## <nombre>` | Simple, robusto al contenido de cada sección; funciona aunque M3/M4/M5 agreguen links | ✅ Elegida |
| Parsear por tabla | Más frágil; el usuario puede editar fuera de la tabla | ❌ |
| Reescritura completa siempre | Destruye links a `.puml` de sesiones anteriores | ❌ |

**How:** El workflow lee el archivo completo, parte por `\n## ` para obtener secciones, las indexa por slug (slugify del heading). Reemplaza las secciones de los grupos procesados, mantiene intactas las demás. Si el parsing no produce al menos una sección por grupo conocido → backup + full rewrite + warning.

---

### Decision: agregar-relacionado re-corre `build_class_diagrams.py` DESPUÉS de persistir

El nuevo grupo debe existir en `funcionalidades/` antes de que el script pueda detectar sus clases como `in_inventory: true`. Por eso el re-run ocurre post-persistencia (Paso 6), no antes.

---

## Data Flow

```
Paso 2 (diff)
  eliminados → clean classes[] in YAMLs → mark desactualizado
  nuevos     → orphan list

Paso 3 (classifier)
  agregar-* → filter inventory: asignadas = union(classes[] de todos los YAMLs)
                                huérfanas  = inventory - asignadas
            → pass huérfanas + existing_functionalities → classifier
  actualizar / nuevo → pass full inventory as before

Paso 3 post (agregar-relacionado, after Paso 4 accepted)
  re-run build_class_diagrams.py --workspace <workspace>
  compare new diagram_candidates/*.yaml vs previous
  groups with changed external_refs → mark artifacts.component_diagrams stale

Paso 6.2 (persist functional_map.md)
  nuevo → full write (existing behavior)
  incremental →
    parse existing file by ## headings
    replace sections of processed groups
    append sections of new groups
    preserve sections of unmodified groups
    fallback: backup + full rewrite + warn
```

## File Changes

| Archivo | Acción | Qué cambia |
|---------|--------|------------|
| `skills/document-xpp/workflows/02-functional-map.md` | Modificar | Paso 2: cleanup eliminados; Paso 3: pre-filter + instrucción a agente + post-agregar-relacionado re-run; Paso 6.2: selective merge |
| `agents/functional-classifier.md` | Modificar | Paso 3: comportamiento diferenciado por modo; contrato JSON: campo `related_to[]` en grupos de agregar-relacionado |
| `CLAUDE.md` | Modificar | Estado M5: "en desarrollo" |

## Interfaces / Contracts

**functional-classifier — nuevo campo `related_to[]` (solo en `agregar-relacionado`):**

```json
{
  "groups": [
    {
      "slug": "billing",
      "name": "Facturación",
      "related_to": ["subscription", "payment"],
      "classes": [ ... ]
    }
  ]
}
```

El campo es opcional: presente solo en `agregar-relacionado`, ausente en los demás modos. El workflow lo usa para marcar las cross-group relationships en los `diagram_candidates`.

## Testing Strategy

| Layer | Qué | Approach |
|-------|-----|----------|
| Manual | Selective merge preserva links `.puml` | Workspace local con functional_map.md que tiene links de M3/M4/M5 |
| Manual | Pre-filter no pasa clases ya asignadas | Ejecutar en workspace con grupos existentes + clases nuevas |
| Manual | Cleanup de eliminados | Remover un `.xpp` del source y verificar que desaparece de `classes[]` |

## Open Questions

- Ninguna — diseño completamente derivado del proposal + specs.
