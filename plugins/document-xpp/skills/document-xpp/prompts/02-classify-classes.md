# Prompt 02 — Clasificar clases y mapear dependencias

**Rol:** arquitecto de soluciones D365 F&O (Senior).

**Objetivo:** tomar los candidatos a grupo funcional del Prompt 01, asignar cada clase del inventario a su grupo, inferir su `role`, y calcular referencias internas y externas usando `dependencies.csv`.

---

## Inputs

- Salida JSON del Prompt 01 (`groups[]` con `candidate_classes`).
- `inventory.csv` completo (ya filtrado por exclusión).
- `dependencies.csv` completo.
- `exclusion-list.md` para filtrar referencias externas.

---

## Pre-requisitos

- Si `groups[]` del Prompt 01 viene vacío, **detenete** y emití un `warnings[]` explicando que no hubo señal suficiente para proponer grupos. No inventes.
- Si `inventory.csv` está vacío, idem.

---

## Procedimiento

### 1. Asignación clase → grupo

Para cada clase en `inventory.csv` (filtrada por exclusión):

1. Buscá en qué `groups[i].patterns` calza.
2. Si **calza en uno solo**: asignala a ese grupo.
3. Si **calza en varios**: elegí el más específico (ej: infijo + nombre específico gana sobre sólo infijo). Registrá en `warnings[]` la ambigüedad.
4. Si **no calza en ninguno**:
   - Intentá clustering por dependencias: si la clase tiene referencias fuertes (≥2) hacia clases de un único grupo, asignala a ese grupo.
   - Si no hay señal clara, mandala a `unclassified[]`.

**No creás grupos nuevos acá.** Si una clase sobra, va a `unclassified` para que el humano decida. Los grupos se crean únicamente en el Prompt 01.

### 2. Inferir `role`

Basado en nombre de clase, `parent`, `interfaces`, y `methods_count` del inventario:

| Rol | Criterio |
|-----|----------|
| `service` | Nombre termina en `Service`, `Manager`, `Handler`, `Orchestrator`, `Facade`. Suele tener `methods_count` alto (>5). |
| `entity` | `parent = Common`, o nombre termina en `Table`, `Entity`, `Record`. Usualmente `methods_count` bajo. |
| `controller` | `parent ∈ { SysOperationController, RunBase, RunBaseBatch }` **y** la clase NO es del ruido técnico. Típicamente trae UI. |
| `dto` | Nombre termina en `Dto`, `Data`, `Contract`, `Response`, `Request`. `methods_count` bajo, sólo getters/setters. |
| `helper` | Nombre termina en `Helper`, `Util`, `Utility`, `Tools`. Métodos estáticos dominantes. |
| `other` | Ninguna de las anteriores. |

Registrá en `warnings[]` cualquier clase donde el rol sea ambiguo.

### 3. Calcular `internal_refs`

Para cada clase clasificada:

```
internal_refs = dependencies.csv
                  .filter(row => row.from_class == clase)
                  .filter(row => row.to_class existe en inventory.csv (columna class))
                  .map(row => row.to_class)
                  .unique()
                  .sorted()
```

### 4. Calcular `external_refs`

```
external_refs = dependencies.csv
                  .filter(row => row.from_class == clase)
                  .filter(row => row.to_class NO existe en inventory.csv)
                  .filter(row => row.to_class NO está en exclusion-list.md)
                  .map(row => row.to_class)
                  .unique()
                  .sorted()
```

### 5. Armar el output final

Combiná la información en el formato contractual del agente (ver `agents/functional-classifier.md` sección "Output"):

```json
{
  "product": "...",
  "mode": "...",
  "groups": [
    {
      "slug": "...",
      "name": "...",
      "description": "...",
      "patterns": [...],
      "classes": [
        {
          "file": "...",
          "class": "...",
          "role": "...",
          "internal_refs": [...],
          "external_refs": [...]
        }
      ]
    }
  ],
  "unclassified": [...],
  "warnings": [...]
}
```

---

## Reglas de calidad

- **Sin duplicados**: una clase vive en **un solo** grupo. Si aparece un conflicto, registrá warning y asignala al grupo con mejor patrón match.
- **Sin grupos vacíos**: si después del Paso 1 algún grupo quedó sin clases, eliminalo del output.
- **Sin clases fantasma**: toda clase en `classes[]` tiene que existir en `inventory.csv`. No inventes.
- **Determinismo**: ordená alfabéticamente `classes` por `class`, `internal_refs` y `external_refs` alfabéticamente. Facilita el diff entre corridas.

---

## Salida

JSON estricto. Sin prosa fuera del bloque. El skill del orquestador lo parsea.
