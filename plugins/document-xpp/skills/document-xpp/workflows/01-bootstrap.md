# Workflow 01 — Bootstrap

**Objetivo:** recolectar los inputs obligatorios, detectar el tipo de sesión y preparar la estructura del workspace antes de cualquier análisis.

Esta fase **siempre** se ejecuta primero y bloquea el avance si falta cualquiera de los inputs obligatorios.

---

## Paso 1 — Recolectar inputs OBLIGATORIOS

Pedí al usuario con `AskUserQuestion` los siguientes datos. Si ya te los pasó en el mensaje inicial, confirmalos explícitamente antes de avanzar.

1. **Ubicación de la carpeta `XppSource`** — path absoluto a la carpeta que contiene los `.xpp` del módulo a documentar.
2. **Directorio del workspace de documentación** — path absoluto donde caerán los entregables. Si no existe, el workflow lo crea.
3. **Tipo de sesión** — una de:
   - `nuevo` — documentación desde cero (sólo válido si el workspace no tiene `_tracking/`).
   - `actualizar` — una o más funcionalidades ya documentadas cambiaron y hay que refrescar los artefactos.
   - `agregar-independiente` — hay una nueva funcionalidad que no se relaciona con las existentes.
   - `agregar-relacionado` — hay una nueva funcionalidad que se vincula con una o más existentes.

### Validación cruzada

- Si `XppSource` no existe o no contiene ningún `.xpp`, informá el error y pedí otra ruta.
- Si el workspace ya tiene `_tracking/`, **no permitas** modo `nuevo`. Listá las funcionalidades previas (leé `_tracking/funcionalidades/*.yaml`) y forzá elegir entre `actualizar` / `agregar-independiente` / `agregar-relacionado`.
- Si el workspace **no** tiene `_tracking/`, el único modo válido es `nuevo`.

---

## Paso 2 — Recolectar inputs OPCIONALES

Preguntá (una sola vez, con `AskUserQuestion`) si el usuario quiere aportar alguno de estos insumos. Todos son opcionales y no bloquean el avance.

- **Documentos de alcance** (paths a archivos Markdown o texto plano). **No se copian** — se registran por path en el YAML de la funcionalidad correspondiente bajo `inputs_registered.scope`.
- **Manuales de usuario** (paths a archivos Markdown o texto plano). **No se copian** — se registran bajo `inputs_registered.manuals`.
- **DBML del modelo de datos** (path a un `.dbml` en formato `dbdiagram.io`). Recomendado: aportalo acá aunque todavía estés en M1 — la Fase 3 (diagramas de clases, M2+) lo va a requerir y pedirlo ahora evita fricción después. Si el usuario aporta:
  - Si ya hay un `.dbml` en `<workspace>/dbml/`, preguntá si sobrescribe o mantiene el existente.
  - Si no hay, **copiá** el archivo a `<workspace>/dbml/` preservando el nombre original.
  - Registrá la ruta relativa resultante (`dbml/<filename>`) — se escribe en `manifest.yaml` bajo `sources.dbml_path` en el Paso 4.
  - Si no aporta, `sources.dbml_path` queda vacío y se pedirá al iniciar Fase 3.
- **Diagramas de clases previos** (paths a `.puml` o `.png`). Si el usuario aporta:
  - **Copiá** cada uno a `<workspace>/adicionales/clases-previas/`.
  - Creá o actualizá `<workspace>/adicionales/README.md` con el disclaimer: *"Insumos de apoyo aportados por el usuario. Pueden estar desactualizados respecto al código vigente; úsese con criterio."*

Si el usuario no aporta nada, seguí adelante sin bloquear.

---

## Paso 3 — Preparar estructura del workspace

Si el modo es `nuevo`, creá esta estructura bajo `<workspace>/`:

```
<workspace>/
  _tracking/
    funcionalidades/          # vacío; se llena en Fase 2
  diagrams/
    classes/                  # vacío; se llena en Fase 3 (M2)
    sequences/                # vacío; se llena en Fase 4 (M4)
    components/               # vacío; se llena en Fase 5 (M3)
  dbml/                       # puede tener el .dbml aportado en Paso 2
  adicionales/                # sólo si se aportaron insumos previos
```

Si el modo **NO** es `nuevo`, verificá que la estructura exista. Si falta alguna carpeta clave (`_tracking/funcionalidades/`), es un tracking corrupto — avisá al usuario y detené el flujo.

---

## Paso 4 — Crear o actualizar `_tracking/manifest.yaml`

Formato:

```yaml
workspace_version: 1
created_at: <ISO-8601 UTC>
last_session_at: <ISO-8601 UTC>
sources:
  xpp_root: <path absoluto a XppSource>
  dbml_path: <ruta relativa al workspace, o "" si no se aportó>
plugin_version: 0.1.0
```

- En modo `nuevo`: creá el archivo con `created_at` = ahora. Escribí `sources.dbml_path` con la ruta registrada en el Paso 2 (o `""` si no se aportó).
- En otros modos: leé el existente y actualizá `last_session_at` = ahora. **No modifiques** `created_at`. Si en esta sesión se aportó un DBML nuevo (o se sobrescribió uno previo), actualizá `sources.dbml_path` en consecuencia.

---

## Paso 5 — Resumen al usuario

Imprimí un resumen breve y confirmalo antes de pasar a Fase 2:

- Modo de sesión.
- Path `XppSource`.
- Path del workspace.
- Inputs opcionales registrados (o *"ninguno"*). Indicá explícitamente si `sources.dbml_path` quedó vacío — en ese caso avisá que Fase 3 lo va a pedir.
- Próxima fase: **02 — Mapa funcional**.

---

## Salida esperada

Al cerrar este workflow:

- `<workspace>/_tracking/manifest.yaml` existe y está al día.
- La estructura de carpetas del workspace está lista.
- En memoria del skill: modo, paths, inputs opcionales. Pasalos al workflow 02.

**No avances** a `workflows/02-functional-map.md` si algún input obligatorio está sin confirmar.
