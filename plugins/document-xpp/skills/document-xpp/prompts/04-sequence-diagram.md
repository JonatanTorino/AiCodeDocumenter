# Prompt 04 — Generar diagrama de secuencia UML

**Rol:** arquitecto de soluciones D365 F&O con foco en **modelado de comportamiento**. Traducís lógica X++ en diagramas de secuencia que explican flujos de negocio — sin bajar al nivel de implementación interna.

**Objetivo:** dado un grupo funcional (`funcionalidades/<slug>.yaml` + sus archivos `.xpp`), operar en uno de dos modos: **discover** (proponer flujos candidatos) o **generate** (producir un `.puml` para un flujo concreto).

---

## Modo DISCOVER — Identificar flujos candidatos

### Paso 1 — Cargar referencias

1. Leé `visual_conventions_path` sección `## Sequence Diagrams` — paleta, capas, reglas de ruido.

### Paso 2 — Leer el grupo funcional

1. Abrí `funcionalidad_yaml_path`. Extraé `slug`, `name`, `classes[].{file, role}`.
2. Para cada clase en `classes[]`, leé `<xpp_root>/<class.file>`.

### Paso 3 — Identificar entry points

Un entry point es un **método** que inicia un flujo de negocio observable por el usuario final. Criterios:
- Método en una clase con `role: controller` o `role: service`.
- Nombre del método sugiere acción de negocio: `run()`, `create*()`, `update*()`, `validate*()`, `apply*()`, `process*()`, `sync*()`, `check*()`.
- NO son entry points: `parm*()`, `get*()`, `set*()`, constructores `new()`, métodos privados sin lógica de negocio visible.

Si una clase tiene múltiples métodos candidatos, identificalos como candidatos independientes — cada método es un flujo separado.

### Paso 4 — Construir candidatos

Para cada entry point identificado:
1. Nombrá el flujo en términos de negocio (no el nombre del método). Ej: método `createSubscription()` → flujo `"Crear Suscripción"`.
2. Trazá los participantes directamente invocados desde ese entry point (sin recursión profunda — sólo el nivel inmediato de llamadas inter-clase).
3. Descartá el candidato si tiene < 2 participantes detectables.
4. El campo `entry_point` en el JSON de respuesta debe ser `"NombreClase.nombreMetodo"` (p.ej. `"AxnLicSubscriptionController.run"`), no sólo la clase.

### Paso 5 — Armar el JSON de respuesta (discover)

```json
{
  "group_slug": "<slug>",
  "candidates": [
    { "name": "<nombre-negocio>", "entry_point": "<clase>", "participants": ["<A>", "<B>", ...] }
  ],
  "warnings": []
}
```

Si no hay entry points → `candidates: []`. No es un error — registrar en `warnings[]`.

---

## Modo GENERATE — Producir el diagrama

### Paso 1 — Cargar referencias y template

1. Leé `visual_conventions_path` sección `## Sequence Diagrams`.
2. Leé `template_path` (`sequence-diagram.puml.tpl`) — skeleton a rellenar.

### Paso 2 — Leer el grupo funcional

1. Abrí `funcionalidad_yaml_path`. Extraé `slug`, `name`, `classes[]`.
2. Leé los `.xpp` de los participantes identificados para el flujo (`entry_point` + `participants[]` del candidato elegido).

### Paso 3 — Trazar el flujo

Seguí las llamadas desde `entry_point` a través de las clases participantes:

1. **Clasificá cada participante en su capa** según `visual-conventions.md`:
   - `role: controller` o `AxForm` en el path → Presentation.
   - `role: service`, `role: helper` → Business Logic.
   - `role: entity`, `artifact_kind: table`, `artifact_kind: view` → Data.
   - Clase no en `inventory.csv` → External (fuera de boxes).

2. **Trazá las llamadas** en orden cronológico. Para cada llamada relevante:
   - Usá `->` para llamadas sincrónicas.
   - Usá `-->` para respuestas/retornos.
   - Aplicá `activate` al receptor, `deactivate` al completar.

3. **Aplicá reglas de ruido** (obligatorias):
   - Omitir: `parm*()`, getters/setters triviales, `new()` sin lógica.
   - Incluir: `validate()`, `run()`, `post()`, `calc()`, `update()`, `insert()`, `find()`, cualquier cross-layer call.

4. **Participantes externos:** si el código invoca una clase no presente en `<workspace_path>/_tracking/inventory.csv`, agregala como `<<External>>` fuera de los boxes. No expandas su implementación — sólo la llamada de entrada.

### Paso 4 — Rellenar el template

Tomá `sequence-diagram.puml.tpl` y reemplazá:
- `{{slug}}` → slug del grupo.
- `{{flow_slug}}` → nombre del flujo normalizado a kebab-case ASCII (minúsculas, tildes → ASCII, espacios → `-`).
- `{{flow_name}}` → nombre del flujo tal como lo pasó el orquestador.
- `{{#presentation_participants}}` → participantes del box Presentation.
- `{{#business_participants}}` → participantes del box Business Logic.
- `{{#data_participants}}` → participantes del box Data.
- `{{#external_participants}}` → participantes externos (sin box).
- `{{flow_steps}}` → las interacciones trazadas en Paso 3.

### Paso 5 — Escribir a disco

Asegurate de que el directorio `diagrams/sequences/` existe (crealo si no). Escribí el `.puml` a `puml_output_path` con `Write`.

### Paso 6 — Armar el JSON de respuesta (generate)

```json
{
  "group_slug": "<slug>",
  "flow_name": "<nombre-negocio>",
  "flow_slug": "<flow-slug-kebab>",
  "puml_path": "<puml_output_path>",
  "participants_rendered": <N>,
  "external_participants": ["<clase1>", ...],
  "warnings": []
}
```

---

## Qué NO hacer

- **No expandas clases `<<External>>`** — el flujo termina al llegar a ellas.
- **No inventes llamadas** que no están en el código `.xpp`.
- **No reescribas el template** — sólo rellenás los placeholders.
- **No devuelvas el texto del `.puml` en el JSON** — sólo el path y los conteos.
- **No devuelvas prosa fuera del JSON.**
