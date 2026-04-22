# Workflow 03 — Diagramas de clases

**Objetivo:** producir un diagrama de clases PlantUML (`.puml`) por cada grupo funcional del workspace, combinando un script determinístico (candidatos por grupo) + el agente `diagram-writer` (decisiones semánticas) + validación humana.

**Prerrequisito:** workflow `02-functional-map.md` cerrado sin bloqueos. El workspace debe tener `_tracking/manifest.yaml`, `_tracking/inventory.csv`, `_tracking/dependencies.csv` y al menos un `_tracking/funcionalidades/<slug>.yaml`.

---

## Paso 1 — Verificar el DBML

La Fase 3 requiere que el DBML del modelo de datos esté disponible — es la fuente de propiedades de tablas/vistas (las `.xpp` sólo tienen comportamientos).

1. Leé `_tracking/manifest.yaml`.
2. Si `sources.dbml_path` está vacío o el archivo referenciado no existe:
   - Pedí el archivo `.dbml` al usuario con `AskUserQuestion` (mismo mecanismo que Fase 1, Paso 2).
   - Copiá a `<workspace>/dbml/` preservando el nombre original.
   - Actualizá `sources.dbml_path` en el manifest. `last_session_at` también se refresca.
3. Validá que el archivo efectivamente existe en disco antes de avanzar. Si no, detené el flujo con mensaje claro.

---

## Paso 2 — Generar candidatos por grupo

Corré el script determinístico — una sola invocación produce un YAML por grupo:

```bash
python "<plugin-root>/skills/document-xpp/scripts/build_class_diagrams.py" \
  --workspace "<workspace>"
```

Efecto esperado:
- Crea o sobrescribe `<workspace>/_tracking/diagram_candidates/<slug>.yaml` — un archivo por cada `funcionalidades/<slug>.yaml`.
- Cada candidato contiene: `nodes[]` (clases del grupo con `artifact_kind` resuelto por path — `class|interface|table|view`), `external_refs[]` (clases referenciadas fuera del grupo, con flag `in_inventory` para distinguir "otro grupo" de "fuera del módulo"), `edges[]` (todas las dependencias filtradas por `exclusion-list.md`).
- El schema está en `references/tracking-schema.md`, sección `_tracking/diagram_candidates/<slug>.yaml`.

Si el script falla, detené el flujo. **No intentes regenerar el candidato a mano** — si el determinístico no corre, el agente no tiene contrato estable que consumir.

---

## Paso 3 — (Sólo modo `actualizar` / `agregar-*`) — Alcance parcial

Si el modo de sesión no es `nuevo`, generar los 7+ diagramas de un módulo grande es innecesario — sólo regenerás los que correspondan a funcionalidades con `status: desactualizado` o `status: nueva` (ver Paso 2 del workflow 02).

1. Leé los `funcionalidades/<slug>.yaml` y listá los `slug` cuyo `status` sea `desactualizado` o `nueva`.
2. Presentá la lista al usuario con `AskUserQuestion`:

   ```
   Funcionalidades con cambios o nuevas desde la última corrida:
     1) <slug-a> (desactualizado)
     2) <slug-b> (nueva)
     ...

   ¿Regenero los diagramas de todas, o elegís un subconjunto?
   ```

3. Guardá la decisión como `grupos_a_regenerar: [slug-a, slug-b, ...]`. Los demás grupos conservan su `.puml` existente.

En modo `nuevo`, saltá este paso: `grupos_a_regenerar` = todos los grupos.

---

## Paso 4 — Delegar al agente `diagram-writer`

Para cada `slug` en `grupos_a_regenerar`, invocá el subagente con `Agent` y `subagent_type: diagram-writer`. Pasale:

- **Path al candidate YAML** (`_tracking/diagram_candidates/<slug>.yaml`) — fuente determinística.
- **Path al workspace** — para que resuelva `xpp_root` y `dbml_path` relativos.
- **Path al `.puml` de salida** — `<workspace>/diagrams/classes/<slug>.puml`. Si ya existe, lo sobrescribe (el `status` del grupo ya justificó la regeneración).
- **Referencias obligatorias** (el agente las lee directamente — no las resumas vos):
  - `references/visual-conventions.md` — reglas de estilo, catálogo de verbos (abierto-curado), paleta.
  - `references/exclusion-list.md` — ya aplicada por el script, pero el agente la valida de nuevo para no emitir nodos ruidosos.

El agente devuelve un JSON con (ver contrato en `agents/diagram-writer.md`):
- `puml_path` — path del `.puml` escrito.
- `warnings[]` — verbos nuevos usados fuera del catálogo, nodos omitidos, cualquier desviación justificada.
- `nodes_rendered`, `edges_rendered` — conteos para sanity-check.

Ejecutá un subagente por grupo de forma secuencial. En paralelo es tentador pero: cada agente lee los `.xpp` completos del grupo + el DBML — mejor ser secuencial para mantener el contexto acotado y detectar fallas temprano.

---

## Paso 5 — Validación humana por diagrama

Por cada `.puml` generado, presentá al usuario:

```
Grupo: <nombre>
Diagrama: <workspace>/diagrams/classes/<slug>.puml
Nodos renderizados: <N>
Aristas: <M>
Warnings del agente:
  - <warning 1>
  - <warning 2>
```

Opciones con `AskUserQuestion`:
- **Aceptar** — pasar al siguiente grupo.
- **Ajustar** — el usuario describe qué modificar (omitir una clase, renombrar un verbo, cambiar estereotipo). Reinvocás al agente con las instrucciones adicionales como override.
- **Rehacer** — volver al Paso 4 con pistas adicionales del usuario.

**Importante:** los warnings por verbos fuera del catálogo NO son errores. Son señal para el usuario de que el catálogo podría crecer. Si el usuario acepta el diagrama con warnings, se persisten tal cual — un PR posterior promueve el verbo al catálogo formal (ver `visual-conventions.md`, sección "Protocolo de evolución").

---

## Paso 6 — Actualizar tracking de funcionalidades

Por cada grupo regenerado, actualizá `_tracking/funcionalidades/<slug>.yaml`:

- `artifacts.class_diagram` = `"diagrams/classes/<slug>.puml"` (path relativo al workspace).
- `status` = `actualizado` (en modo incremental) o `nueva` → `actualizado` si era la primera pasada.
- `last_updated` = ahora (ISO-8601 UTC).

---

## Paso 7 — Actualizar `functional_map.md`

Agregá un link al `.puml` generado en la fila del grupo correspondiente. Formato:

```markdown
## <Nombre del grupo>

**Descripción:** <una línea>
**Diagrama de clases:** [<slug>.puml](diagrams/classes/<slug>.puml)

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| ... | ... | ... |
```

Si el grupo no se regeneró en esta sesión pero ya tenía un `.puml` de sesiones anteriores, el link se conserva.

---

## Paso 8 — Resumen al usuario

Imprimí:

- Cantidad de diagramas generados en esta sesión.
- Cantidad de diagramas conservados (modo incremental).
- Warnings agregados (verbos nuevos fuera del catálogo + nodos omitidos).
- Ruta del `functional_map.md` actualizado.
- Próxima fase: **04 — Diagramas de componentes (C4 — M3, no disponible todavía)**.

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/diagrams/classes/<slug>.puml` existe para cada grupo regenerado.
- `<workspace>/_tracking/diagram_candidates/<slug>.yaml` refleja el último candidato emitido.
- `<workspace>/_tracking/funcionalidades/<slug>.yaml` tiene `artifacts.class_diagram` apuntando al `.puml`.
- `<workspace>/functional_map.md` linkea cada `.puml` desde el grupo correspondiente.

**No avances** a Fase 4 hasta que M3 esté implementado. M2 cierra acá.
