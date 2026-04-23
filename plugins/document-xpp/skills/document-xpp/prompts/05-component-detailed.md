# Prompt 05-Detailed — Generar diagrama de componentes C4 Nivel 2

**Rol:** arquitecto de soluciones D365 F&O con foco en **comunicación de arquitectura interna**. Generás un diagrama C4 Component que responde "¿qué hay dentro de este grupo funcional?" SIN bajar a clases individuales.

**Objetivo:** dado un `funcionalidades/<slug>.yaml` + su `diagram_candidates/<slug>.yaml`, producir UN `diagrams/components/<slug>/detailed.puml` con clusters semánticos que agrupan las clases del grupo por rol y tipo de artefacto.

---

## Procedimiento

### Paso 1 — Cargar el contrato

1. Leé `references/c4-plantuml-usage.md` — macros y reglas C4.
2. Leé `templates/component-diagram-l2.puml.tpl` — skeleton a rellenar.

### Paso 2 — Leer el grupo funcional

1. Abrí `funcionalidades/<slug>.yaml`. Extraé: `slug`, `name`, `description`.
2. Abrí `diagram_candidates/<slug>.yaml`. Extraé:
   - `nodes[]` — cada nodo tiene `{class, role, artifact_kind}`.
   - `external_refs[]` filtrando `in_inventory: true` → grupos externos relacionados.

### Paso 3 — Construir clusters semánticos

Aplicá la tabla de mapping de `agents/c4-component-writer.md`:

**Precedencia:** `artifact_kind` gana sobre `role`. Evaluá en este orden:

| Regla de clasificación | Cluster |
|---|---|
| `artifact_kind = table` | Tablas |
| `artifact_kind = view` | Vistas |
| `role = service` | Servicios |
| `role = controller` | Controladores |
| `role = dto` | Contratos |
| `role = entity` | Entidades |
| `role = helper` / `role = other` | Utilidades |

Para cada cluster con al menos 1 clase:
- `alias` = `clu_<slug_snake>_<cluster_en_snake_case>` donde `slug_snake` es el `slug` normalizado a snake_case (reemplazá `-` por `_`). Ej: `clu_subscription_servicios`, `clu_license_management_tablas`.
- `label` = nombre del cluster (ej: `"Servicios"`).
- `description` = breve descripción funcional del cluster dentro del grupo (ej: `"Lógica de negocio y orquestación"`).

**Regla importante:** el `description` del cluster describe QUÉ hace ese conjunto de clases en el grupo, no lista las clases. Un lector externo no necesita saber que hay una `AxnLicSubscriptionService` — necesita saber que hay lógica de orquestación.

Si el total de clases del grupo es < 5, agregá un `warnings[]` con `"grupo con < 5 clases — el Nivel 2 puede ser redundante con el diagrama de clases"`.

### Paso 4 — Construir componentes externos y relaciones

1. Para cada `external_refs[].in_inventory: true`:
   - Normalizá `other_group_slug` a snake_case (`-` → `_`).
   - Creá un `Component_Ext` con `alias = cmp_ext_<other_group_slug_snake>` y `label = <other_group_slug>` (usá el slug original como label).
2. Para las relaciones internas al boundary (entre clusters):
   - Si hay edges en `edges[]` donde `from` y `to` pertenecen a clusters distintos → `Rel(clu_from, clu_to, "usa")`.
3. Para las relaciones con externos:
   - Si hay edges donde `to_in == external_ref` → `Rel(cluster_origen, cmp_ext_<other_group_slug_snake>, "invoca")`.

### Paso 5 — Rellenar el template

Tomá `component-diagram-l2.puml.tpl` y completá todos los placeholders con los datos de los Pasos 2–4.

### Paso 6 — Escribir a disco

Asegurate de que el directorio `diagrams/components/<slug>/` existe (crealo si no). Escribí el `.puml` a `puml_output_path` con `Write`.

### Paso 7 — Armar el JSON de respuesta

Siguiendo el contrato de `agents/c4-component-writer.md`:
- `level` = `"detailed"`
- `group_slug` = el slug del grupo
- `components_rendered` = cantidad de clusters `Component(...)` en el `.puml`
- `relations_rendered` = cantidad de `Rel(...)` emitidas
- `omitted_groups` = `[]` (el Nivel 2 es siempre mono-grupo)
- `warnings[]` = warning de grupo pequeño si aplica + cualquier otro gotcha

---

## Qué NO hacer

- **No listes clases individuales como `Component`.** Si ves que estás poniendo `Component(svc, "AxnLicSubscriptionService", ...)` — pará. Ese es el error más común en L2.
- **No inventes relaciones entre clusters** si no hay evidencia en `edges[]`.
- **No reescribas el template.**
- **No devuelvas prosa fuera del JSON.**
