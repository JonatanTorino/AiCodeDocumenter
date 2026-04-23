# Workflow 04 — Diagramas de secuencia UML

**Objetivo:** producir diagramas UML de secuencia para los flujos de negocio de un grupo funcional, combinando lectura directa del código `.xpp` + el agente `sequence-diagram-writer` (discovery interactivo + generación) + validación humana.

**Prerrequisito:** workflows `01-bootstrap.md` y `02-functional-map.md` cerrados sin bloqueos. El workspace debe tener `_tracking/manifest.yaml` y al menos un `_tracking/funcionalidades/<slug>.yaml`.

---

## Paso 1 — Verificar prerrequisitos

1. Verificá que existe `<workspace>/_tracking/funcionalidades/` con al menos un YAML.
2. Si NO existe o está vacío:
   ```
   Fase 4 requiere funcionalidades documentadas. Corré primero las Fases 1 y 2.
   ```
   Detené el flujo.
3. Leé cada YAML y evaluá su `status`. Si hay grupos con `status: desactualizado`, advertí al usuario con `AskUserQuestion`:
   ```
   Los siguientes grupos tienen cambios pendientes: <lista>
   Podés continuar, pero los diagramas de secuencia reflejarán el código anterior al cambio.
   ¿Continuás igual o preferís actualizar primero?
   ```
   Si elige actualizar, detené el flujo y recomendá correr Fases 2-3 primero.
4. Leé `<workspace>/_tracking/manifest.yaml`. Extraé `sources.xpp_root` — lo usarás en todos los pasos siguientes. Si `xpp_root` está vacío o el directorio no existe, detené el flujo con mensaje claro.

---

## Paso 2 — Seleccionar grupo funcional

1. Listá todos los `slug` en `_tracking/funcionalidades/`.
2. Si hay más de un grupo, presentá la lista al usuario con `AskUserQuestion`:

   ```
   Grupos funcionales disponibles:
     1) <slug-a> — <name>
     2) <slug-b> — <name>
     ...

   ¿Para qué grupo querés generar diagramas de secuencia?
   ```

3. Si hay un solo grupo, seleccionalo automáticamente e informá al usuario.
4. Guardá `grupo_elegido = <slug>` y `funcionalidad_yaml_path = <workspace>/_tracking/funcionalidades/<slug>.yaml`.

---

## Paso 3 — Discovery: identificar flujos candidatos

Invocá el agente con `Agent` y `subagent_type: sequence-diagram-writer`. Pasale:

- `mode`: `"discover"`
- `funcionalidad_yaml_path`: path del YAML elegido en Paso 2
- `xpp_root`: obtenido del manifest en Paso 1
- `workspace_path`: `<workspace>`
- `prompt_path`: `<plugin-root>/skills/document-xpp/prompts/04-sequence-diagram.md`
- `visual_conventions_path`: `<plugin-root>/skills/document-xpp/references/visual-conventions.md`

El agente devuelve JSON con `candidates[]` y `warnings[]`.

Si `candidates` está vacío:
```
El agente no encontró entry points de negocio en el grupo "<slug>".
Podés describir manualmente el flujo que querés diagramar, o saltar a Fase 5.
```
Presentá con `AskUserQuestion` y esperá la decisión.

---

## Paso 4 — Selección interactiva de flujos

Presentá los candidatos al usuario con `AskUserQuestion`:

```
Flujos candidatos detectados en "<name>":
  1) <nombre-flujo-1> — entry point: <clase>, participantes: <A>, <B>, <C>
  2) <nombre-flujo-2> — entry point: <clase>, participantes: <A>, <B>
  ...

¿Cuáles querés diagramar? (número/s, "todos", o describí un flujo personalizado)
```

Guardá la lista de flujos a generar como `flujos_a_generar: [...]`.

Si el usuario describe un flujo personalizado (no en la lista), agregalo a `flujos_a_generar` con los datos que el usuario provea (`name`, `entry_point`).

---

## Paso 5 — Generación y validación por flujo

Para cada flujo en `flujos_a_generar`, ejecutá secuencialmente:

### 5a — Calcular flow-slug

Normalizá `flow_name` a kebab-case ASCII:
- Minúsculas.
- Tildes → ASCII: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `ñ→n`, `ü→u`.
- Espacios y caracteres especiales → `-`.
- Ejemplo: `"Crear Suscripción"` → `crear-suscripcion`.

### 5b — Invocar agente (generate)

Invocá el agente con `Agent` y `subagent_type: sequence-diagram-writer`. Pasale:

- `mode`: `"generate"`
- `funcionalidad_yaml_path`: path del YAML del grupo
- `xpp_root`: obtenido del manifest
- `workspace_path`: `<workspace>`
- `template_path`: `<plugin-root>/skills/document-xpp/templates/sequence-diagram.puml.tpl`
- `prompt_path`: `<plugin-root>/skills/document-xpp/prompts/04-sequence-diagram.md`
- `visual_conventions_path`: `<plugin-root>/skills/document-xpp/references/visual-conventions.md`
- `flow_name`: nombre del flujo
- `entry_point`: método entry point en formato `Clase.metodo` (p.ej. `"AxnLicSubscriptionController.run"`)
- `puml_output_path`: `<workspace>/diagrams/sequences/<slug>-<flow-slug>.puml`

### 5c — Validación humana

Presentá al usuario con `AskUserQuestion`:

```
Diagrama: diagrams/sequences/<slug>-<flow-slug>.puml
Flujo: <flow_name>
Participantes: <participants_rendered>
Externos: <external_participants>
Warnings del agente:
  - <warning 1>
  - ...
```

Opciones:
- **Aceptar** — avanzar al siguiente flujo.
- **Ajustar** — el usuario describe la corrección. Reinvocás el agente con las instrucciones adicionales como override en el prompt.
- **Rehacer** — volver al paso 5b desde cero.

### 5d — Actualizar tracking

Si el usuario aceptó, actualizá `_tracking/funcionalidades/<slug>.yaml`:

```yaml
artifacts:
  sequence_diagrams:
    - name: "<flow_name>"
      file: "diagrams/sequences/<slug>-<flow-slug>.puml"
```

- Si `artifacts.sequence_diagrams` no existe, crealo.
- Si ya existe, **agregá** la nueva entrada sin eliminar las anteriores.
- Verificá que no queden entradas duplicadas (mismo `name` y `file`).
- Actualizá `last_updated` a la fecha/hora actual (ISO-8601 UTC).
- Si `status` era `nueva` o `desactualizado`, actualizalo a `actualizado`.

---

## Paso 6 — Resumen al usuario

Imprimí:

- Cantidad de diagramas generados en esta sesión.
- Flujos omitidos (si el usuario eligió un subconjunto).
- Warnings agregados.
- Paths de los `.puml` generados.
- Próxima fase: **05 — Diagramas de componentes C4** (`workflows/05-component-diagrams.md`).

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/diagrams/sequences/<slug>-<flow-slug>.puml` existe para cada flujo generado.
- `<workspace>/_tracking/funcionalidades/<slug>.yaml` tiene `artifacts.sequence_diagrams` populado.
