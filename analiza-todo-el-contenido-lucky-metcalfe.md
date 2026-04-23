# Plan: MVP de AiCodeDocumenter como plugin de Claude Code

## Contexto

Hoy `AiCodeDocumenter/` es una colección de 7 prompts bien escritos (`Prompts/00_identify_functional_groups.md` a `Prompts/05_generate_sequence_diagrams.md`) más `GuiaParaDocTecnica.md` que orquesta todo a mano. El humano pega los prompts en una sesión de IA, mantiene la sesión abierta para preservar contexto, y arma los artefactos uno por uno.

**Problema**: el valor conceptual está resuelto (rúbricas, estilos, flujo), pero no hay herramienta que lo ejecute. Todo depende de disciplina humana y de que la sesión de IA no se corte.

**Objetivo del MVP**: plugin de Claude Code (`document-xpp`) instalado en `~/.claude/plugins/` que guíe al usuario punta a punta, soporte documentación desde cero y actualización incremental, y deje todos los artefactos en un workspace con estructura convencional.

**Fuera de alcance (explícito)**:
- Conversión XML→XPP (ya manual, out-of-scope — el flujo arranca con `XppSource/` ya poblada).
- AiCodeReviewer, Pipelines, CI/CD.
- Render PlantUML a PNG/SVG (sólo se entregan `.puml`).
- Histórico de `.xpp` (siempre se trabaja contra la versión vigente).

---

## Decisión: skills vs agentes vs pipelines

**Plugin con un skill interactivo maestro + subagentes puntuales**. Razones:

- El flujo **requiere decisiones humanas en cada fase** (validar mapa funcional, elegir flujos de secuencia, aportar insumos opcionales). Eso descarta pipelines CI/CD.
- Las fases que procesan cientos de `.xpp` (scanner, clasificador) se delegan a **subagentes** para no saturar el hilo principal de Claude.
- El skill maestro ES el orquestador ligero — no hace falta infra de orquestación adicional.
- Pipelines recién tendrán sentido cuando el flujo sea 100% determinístico (post-MVP).

---

## Skills/Plugins externos a reusar

| Necesidad | Solución | Acción |
|---|---|---|
| Generar C4-PlantUML (componentes, contenedores, contexto) | `anthropic-skills:c4-plantuml` (ya instalado localmente) | Invocarlo desde el workflow de componentes |
| Sintaxis PlantUML para clases, secuencia y C4 | `melodic-software/claude-code-plugins@visualization` (incluye skills `plantuml-syntax`, `diagram-patterns`, `mermaid-syntax` + agents `diagram-generator` y `code-visualizer`) | Declarar vía `extraKnownMarketplaces` + `enabledPlugins` en `.claude/settings.json` del repo (B-prime). Detalle en `M0.2-investigacion-plugin-uml/03-decision.md` |
| Alternativa a C4 si preferís otra librería | `softaworks/agent-toolkit@c4-architecture` (3.6K installs) | Back-up, no usar de arranque |

Acción al inicio de M1: declarar `visualization@melodic-software` en `.claude/settings.json` del repo. Un solo skill cubre los 4 tipos de diagramas que necesita `document-xpp` (clases, secuencia, componentes C4, contenedores C4). Si la calidad del output no alcanza, evaluar migración al par `bitsmuggler/c4-skill` + `SpillwaveSolutions/plantuml` en una iteración posterior.

---

## Arquitectura del plugin

### Estructura del marketplace local + plugin (dentro del repo)

El repo `AiCodeDocumenter/` actúa como **marketplace local** de Claude Code. Un único plugin `document-xpp` vive bajo `plugins/`. Para que un compañero lo use, clona el repo e instala desde Claude Code:

```bash
# Desde Claude Code (cualquier CWD)
/plugin marketplace add <path-al-clone-local-o-url-git-del-repo>
/plugin install document-xpp@<marketplace-name>
```

Ventaja: el plugin viaja con git, es versionable y reviewable en PRs, y sirve tanto desde Claude Code local como remoto.

Estructura:

```
AiCodeDocumenter/                           # raíz del repo = marketplace local
  .claude-plugin/
    marketplace.json                        # manifiesto del marketplace (lista document-xpp)
  plugins/
    document-xpp/
      plugin.json                           # manifiesto del plugin
      skills/
        document-xpp/
          SKILL.md                          # entry point del skill maestro
          workflows/
            01-bootstrap.md                 # Fase 1: inputs obligatorios + detección de modo
            02-functional-map.md            # Fase 2: scanner + clasificador + mapa
            03-class-diagrams.md            # Fase 3: UML de clases por grupo
            04-sequence-diagrams.md         # Fase 4: secuencia interactiva
            05-component-diagrams.md        # Fase 5: C4 dos niveles
          prompts/
            01-identify-functional-groups.md  # NUEVOS, escritos desde cero
            02-classify-classes.md
            03-class-diagram.md
            04-sequence-diagram.md
            05-component-conceptual.md
            05-component-detailed.md
          references/
            exclusion-list.md               # dominios técnicos a ignorar (NUEVO, desde cero)
            tracking-schema.md              # schema de YAML + CSV
            c4-plantuml-usage.md            # cómo invocar el skill anthropic:c4-plantuml
            visual-conventions.md           # colores, naming, estilos (derivado de GuiaParaDocTecnica)
          templates/
            tracking-funcionalidad.yaml.tpl
            hashes.csv.tpl
            adicionales-README.md.tpl
          scripts/
            Compute-XppHashes.ps1           # barrido MD5 + size + mtime → hashes.csv
            Build-XppInventory.ps1          # parsea .xpp → inventory.csv + dependencies.csv
      agents/
        functional-classifier.md            # ÚNICO agente en Fase 2 — interpreta salida de scripts
        diagram-writer.md                   # genera .puml por grupo/flujo

  # --- LEGACY (intacto durante desarrollo; se elimina al cerrar el MVP) ---
  Prompts/ Output/ .Drafts/ Tests/
  GuiaParaDocTecnica.md  GEMINI.md  README.md
```

**Aislamiento estricto**: el trabajo NUEVO vive exclusivamente bajo `.claude-plugin/` y `plugins/document-xpp/`. Los archivos viejos quedan intactos durante el desarrollo y al cerrar el MVP se eliminan de una sola pasada — sin mover nada, sin mezclas.

**Separación determinístico vs semántico**: todo lo que se puede resolver con parseo (clases, métodos, referencias, prefijos, hashes, diffs) vive en `scripts/` como PowerShell. El LLM entra sólo cuando hay juicio semántico (agrupar funcionalmente, generar diagramas que comuniquen intención). Esto hace el flujo más rápido, reproducible y auditable.

Todos los prompts en `skills/document-xpp/prompts/` son **nuevos, escritos desde cero**. Los originales de `AiCodeDocumenter/Prompts/` se leen al inicio SÓLO para entender propósito y convenciones del dominio. No se copian, no se incluyen, y **no se modifican**.

### Estructura del workspace de documentación (salida)

Los **inputs externos (alcance, manuales)** viven donde el usuario los tenga — fuera del workspace — y sólo se registran por path en el tracking. Los **insumos técnicos (DBML, diagramas previos)** sí se copian al workspace.

```
<workspace>/
  functional_map.md                   # resumen human-readable, pivote
  _tracking/
    manifest.yaml                     # metadata general del workspace (versión, fecha, fuentes)
    hashes.csv                        # barrido actual de XppSource (MD5 + size + mtime)
    hashes.previous.csv               # barrido anterior, usado para diff en modo actualización
    funcionalidades/
      <nombre-funcionalidad>.yaml     # UN yaml por cada funcionalidad documentada
  diagrams/
    classes/<grupo>.puml
    sequences/<grupo>-<flujo>.puml
    components/
      conceptual.puml                 # nivel 1: todo el sistema (un solo archivo)
      <grupo>/detailed.puml           # nivel 2: refinamiento por grupo
  dbml/
    modelo.dbml                       # copia; si el usuario no aporta, se pide
  adicionales/
    README.md                         # disclaimer: "insumos de apoyo, pueden estar desactualizados"
    clases-previas/                   # diagramas de clases previos si fueron aportados
    otros/                            # cualquier otro insumo técnico que el user quiera preservar
```

### Schema del tracking (un YAML por funcionalidad)

```yaml
# <workspace>/_tracking/funcionalidades/subscription.yaml
name: Subscription
slug: subscription
description: "Gestión del ciclo de vida de suscripciones"
created_at: 2026-04-17T10:00:00
last_updated: 2026-04-17T10:00:00
status: actualizado           # actualizado | desactualizado | nueva

classes:
  - file: AxnLicSubscriptionService.xpp
    role: service
  - file: AxnLicSubscription.xpp
    role: entity

inputs_registered:
  # rutas externas al workspace; sólo se guardan las rutas, no se copia el contenido
  scope:
    - K:/docs/subscription-scope.md
  manuals:
    - K:/manuals/subscription-user-manual.md
  previous_diagrams:                  # si se aportan, se copian a adicionales/clases-previas/
    - K:/legacy/subscription-classes.puml

artifacts:
  class_diagram: diagrams/classes/subscription.puml
  sequence_diagrams:
    - name: "Crear suscripción"
      file: diagrams/sequences/subscription-crear.puml
  component_diagrams:
    level_1_node_in: diagrams/components/conceptual.puml   # participa en el nivel 1 global
    level_2: diagrams/components/subscription/detailed.puml
```

### Schema del archivo de hashes (CSV separado)

```csv
# <workspace>/_tracking/hashes.csv
file,size,mtime,md5
subs/AxnLicSubscription.xpp,1024,1734567890,abc123def456...
subs/AxnLicSubscriptionService.xpp,2048,1734567891,fed654cba321...
```

- `file` es la ruta relativa a la raíz de `XppSource`.
- `mtime` en epoch Unix.
- `md5` del contenido binario del archivo (rápido, determinístico, cross-machine).

---

## Estrategia de hashing

**Algoritmo**: MD5 sobre el contenido del archivo.
- Rápido (miles de archivos por segundo).
- Determinístico y cross-platform (Windows, WSL, Linux).
- No usamos SHA256 porque no hay amenaza de colisión adversarial — sólo detección de cambios.
- NO usamos `size+mtime` como fast-path porque falsea positivos si el user hace `touch` o checkout en otra máquina.

**Script responsable**: `scripts/Compute-XppHashes.ps1` (PowerShell).

**Responsabilidad**: el skill lo invoca vía la herramienta Bash al inicio de cada sesión. Salida: sobrescribe `_tracking/hashes.csv`. Antes de sobrescribir, si existía, lo mueve a `_tracking/hashes.previous.csv`.

**Cuándo se corre**:
1. **Sesión nueva** (no hay tracking): se genera `hashes.csv` de cero. No hay `hashes.previous.csv`.
2. **Sesión de actualización**: se renombra `hashes.csv` → `hashes.previous.csv`, se regenera `hashes.csv` barriendo TODO `XppSource`, y se diffean.

**Lógica de diff** (en el workflow 02):
1. Archivos en `hashes.csv` con md5 distinto a `hashes.previous.csv` → marcar como **modificados**.
2. Archivos nuevos en `hashes.csv` (no existían antes) → marcar como **nuevos/huérfanos** (a clasificar).
3. Archivos que estaban en `hashes.previous.csv` y ya no están → marcar como **eliminados**.
4. Cruzar con los `<funcionalidad>.yaml`: cualquier funcionalidad que tenga una clase modificada o eliminada se marca `status: desactualizado`.
5. Archivos nuevos huérfanos se ofrecen al usuario para asignar: (a) funcionalidad existente, (b) nueva funcionalidad independiente, (c) nueva funcionalidad relacionada.

**Importante**: aunque exista tracking previo, SIEMPRE se barre la carpeta `XppSource` completa para detectar archivos nuevos o dependencias agregadas que no estaban referenciadas en ninguna funcionalidad.

---

## Flujo del skill (Fases 1 a 5)

### Fase 1 — Bootstrap (obligatoria siempre)

**Inputs OBLIGATORIOS (bloquean si faltan)**:
1. Ubicación de la carpeta `XppSource` con los `.xpp`.
2. Directorio del workspace de documentación.
3. Tipo de sesión:
   - `nuevo` — documentación desde cero (sólo válido si no existe `_tracking/` en el workspace).
   - `actualizar` — una funcionalidad documentada cambió.
   - `agregar-independiente` — nueva funcionalidad que no se relaciona con las existentes.
   - `agregar-relacionado` — nueva funcionalidad que se vincula con una o más existentes.

Si el workspace ya tiene `_tracking/`, el skill lista las funcionalidades previas y fuerza elegir entre `actualizar` / `agregar-independiente` / `agregar-relacionado`.

**Inputs OPCIONALES (no bloquean)**:
- Documentos de alcance: el user aporta rutas. Se registran en `inputs_registered.scope` del YAML correspondiente. NO se copian.
- Manuales de usuario: idem anterior, registrados como `inputs_registered.manuals`.
- DBML: si está en `<workspace>/dbml/`, se usa. Si está afuera, se COPIA a `<workspace>/dbml/`. Si no existe, el skill lo pide; si el user no lo tiene, la fase avanza sin DBML.
- Diagramas de clases previos: si se aportan, se COPIAN a `<workspace>/adicionales/clases-previas/` y se crea/actualiza `<workspace>/adicionales/README.md` con el disclaimer.

### Fase 2 — Mapa funcional

1. El skill corre **`Compute-XppHashes.ps1`** sobre `XppSource` → `_tracking/hashes.csv`.
2. El skill corre **`Build-XppInventory.ps1`** sobre `XppSource` → `_tracking/inventory.csv` + `_tracking/dependencies.csv`.
   - `inventory.csv`: `file, class, parent, interfaces, methods_count, prefix`
   - `dependencies.csv`: `from_class, to_class, kind` donde `kind ∈ {extends, implements, uses, calls}`
3. Subagente `functional-classifier` lee `inventory.csv`, `dependencies.csv`, `references/exclusion-list.md` y (si están registrados) los documentos de `inputs_registered.scope/manuals`. Aplica `prompts/01-identify-functional-groups.md` + `prompts/02-classify-classes.md` → propone grupos funcionales.
4. El skill presenta el mapa propuesto al user con AskUserQuestion para validar/ajustar.
5. Persiste `functional_map.md` y genera/actualiza los `funcionalidades/<nombre>.yaml`.
6. **Modo actualización**: compara hashes (ver sección de hashing) → marca cada funcionalidad con su status y reporta archivos huérfanos.

**Por qué un solo agente**: las dependencias y la estructura ya vienen resueltas de los scripts. El agente NO descubre — sólo agrupa con criterio semántico. Esto evita duplicación de trabajo entre un "scanner" y un "classifier" (como había en la v1 del plan) y reduce el costo de LLM al mínimo necesario.

### Fase 3 — Diagramas de clases

- Por cada funcionalidad con status `nueva` o `desactualizado` (o las que el user elija forzar): subagente `diagram-writer` aplica `prompts/03-class-diagram.md` → `diagrams/classes/<grupo>.puml`.
- En modo `actualizar`, NO regenera grupos `actualizado` salvo flag explícito.
- Usa el skill externo de UML instalado para la sintaxis PlantUML correcta.

### Fase 4 — Diagramas de secuencia (interactivo)

- Skill analiza código + rutas registradas en `inputs_registered.scope` e `inputs_registered.manuals` para detectar flujos candidatos.
- Pregunta al user con AskUserQuestion: "Detecté estos flujos: A, B, C. ¿Cuáles querés diagramar?"
- Para cada flujo elegido: subagente `diagram-writer` aplica `prompts/04-sequence-diagram.md` → `diagrams/sequences/<grupo>-<flujo>.puml`.
- Registra el nombre y path en el YAML de la funcionalidad.

### Fase 5 — Diagramas de componentes C4 (dos niveles)

- Invoca el skill `anthropic-skills:c4-plantuml` para generar con sintaxis C4-PlantUML oficial.
- **Nivel 1 (conceptual, un solo archivo)**: un componente por grupo funcional, relaciones entre grupos. Archivo: `diagrams/components/conceptual.puml`. Aplica `prompts/05-component-conceptual.md`.
- **Nivel 2 (detallado, uno por grupo)**: para cada grupo, refina componentes internos SIN bajar a clases individuales. Archivo: `diagrams/components/<grupo>/detailed.puml`. Aplica `prompts/05-component-detailed.md`.
- El prompt `04_generate_container_diagram.md` original NO se replica; queda como referencia histórica en el repo.

---

## Uso de los `.md` originales como referencia conceptual

Antes de escribir los prompts nuevos del plugin, se leen los `.md` existentes de `AiCodeDocumenter/` (Prompts/00..05, exclusion_list, GuiaParaDocTecnica, GEMINI.md) para entender:
- Qué problema resuelve cada paso.
- Qué criterio aplican (qué consideran ruido, qué consideran funcionalidad, qué convenciones visuales).
- Qué entradas y salidas esperan.

**No se modifican, no se copian, no se mantienen versiones mejoradas.** Sirven sólo como base conceptual para los prompts NUEVOS que escribimos desde cero en `skills/document-xpp/prompts/`.

---

## Entregas incrementales (M1 → M5)

| Hito | Entregable | Soporta |
|---|---|---|
| **M0** | Lectura de los `.md` originales como referencia conceptual. Instalación del skill externo de UML. Validación del parser X++ sobre un módulo de prueba. | Preparación del terreno. |
| **M1** | `plugin.json` + `SKILL.md` + `workflows/01-bootstrap.md` + `workflows/02-functional-map.md` + agente `functional-classifier` + scripts `Compute-XppHashes.ps1` y `Build-XppInventory.ps1` + templates de tracking + prompts 01 y 02 + `references/exclusion-list.md`. | `nuevo` + detección de workspace existente con diff de hashes y barrido de inventario. |
| **M2** | `workflows/03-class-diagrams.md` + agente `diagram-writer` + prompt `03-class-diagram.md`. | Diagramas de clases por grupo. |
| **M3** | `workflows/05-component-diagrams.md` + prompts `05-component-conceptual.md` y `05-component-detailed.md` + integración con `anthropic-skills:c4-plantuml`. | Diagramas de componentes C4 nivel 1 y 2. |
| **M4** | `workflows/04-sequence-diagrams.md` interactivo + prompt `04-sequence-diagram.md`. | Diagramas de secuencia. |
| **M5** | Soporte completo `actualizar` + `agregar-independiente` + `agregar-relacionado` con diffing fino y orfandad. | Iteración sobre workspace existente. |

Cada hito es entregable por sí solo.

---

## Archivos clave a crear (rutas exactas, relativas a la raíz del repo)

- `.claude-plugin/marketplace.json` — manifiesto del marketplace local (declara el plugin `document-xpp`)
- `plugins/document-xpp/plugin.json`
- `plugins/document-xpp/skills/document-xpp/SKILL.md`
- `plugins/document-xpp/skills/document-xpp/workflows/01-bootstrap.md`
- `plugins/document-xpp/skills/document-xpp/workflows/02-functional-map.md`
- `plugins/document-xpp/skills/document-xpp/workflows/03-class-diagrams.md`
- `plugins/document-xpp/skills/document-xpp/workflows/04-sequence-diagrams.md`
- `plugins/document-xpp/skills/document-xpp/workflows/05-component-diagrams.md`
- `plugins/document-xpp/skills/document-xpp/prompts/01-identify-functional-groups.md`
- `plugins/document-xpp/skills/document-xpp/prompts/02-classify-classes.md`
- `plugins/document-xpp/skills/document-xpp/prompts/03-class-diagram.md`
- `plugins/document-xpp/skills/document-xpp/prompts/04-sequence-diagram.md`
- `plugins/document-xpp/skills/document-xpp/prompts/05-component-conceptual.md`
- `plugins/document-xpp/skills/document-xpp/prompts/05-component-detailed.md`
- `plugins/document-xpp/skills/document-xpp/references/exclusion-list.md`
- `plugins/document-xpp/skills/document-xpp/references/tracking-schema.md`
- `plugins/document-xpp/skills/document-xpp/references/c4-plantuml-usage.md`
- `plugins/document-xpp/skills/document-xpp/references/visual-conventions.md`
- `plugins/document-xpp/skills/document-xpp/templates/tracking-funcionalidad.yaml.tpl`
- `plugins/document-xpp/skills/document-xpp/templates/hashes.csv.tpl`
- `plugins/document-xpp/skills/document-xpp/templates/adicionales-README.md.tpl`
- `plugins/document-xpp/skills/document-xpp/scripts/Compute-XppHashes.ps1` — MD5 + size + mtime → `hashes.csv`
- `plugins/document-xpp/skills/document-xpp/scripts/Build-XppInventory.ps1` — parsea `.xpp` → `inventory.csv` + `dependencies.csv`
- `plugins/document-xpp/agents/functional-classifier.md` — único agente en Fase 2
- `plugins/document-xpp/agents/diagram-writer.md` — genera `.puml` en Fases 3, 4 y 5

Los `.md` originales del repo NO se modifican. Se leen como referencia conceptual y punto.

---

## Verificación (end-to-end al cerrar M1)

1. Registrar el marketplace local apuntando a la raíz del repo clonado: `/plugin marketplace add <path-al-repo-AiCodeDocumenter>`.
2. Instalar el plugin: `/plugin install document-xpp@<marketplace-name>`. Verificar que aparezca `/document-xpp` en el autocomplete.
3. Crear un workspace de prueba vacío, por ejemplo `D:/docs/license-test/`.
4. Apuntar a un `XppSource` real (ej: módulo Licencias con ~50-100 archivos).
5. Ejecutar `/document-xpp`.
6. Validar Fase 1:
   - Skill pide ubicación `XppSource` y workspace, bloquea si faltan.
   - Detecta que el workspace no tiene `_tracking/` → fuerza modo `nuevo`.
   - Crea estructura de carpetas del workspace.
7. Validar Fase 2:
   - Corre `Compute-XppHashes.ps1`, genera `_tracking/hashes.csv`.
   - Corre scanner + classifier, propone grupos.
   - User valida con AskUserQuestion, persiste `functional_map.md` y un `funcionalidades/<nombre>.yaml` por grupo.
8. Modificar un `.xpp` en `XppSource`, re-ejecutar `/document-xpp` sobre el mismo workspace.
9. Validar:
   - Detecta `_tracking/` existente → pregunta modo (excluyendo `nuevo`).
   - En `actualizar`, renombra `hashes.csv` a `hashes.previous.csv`, regenera `hashes.csv`, diffea.
   - Marca la funcionalidad afectada como `status: desactualizado`.
   - Si hay archivos nuevos en `XppSource`, los reporta como huérfanos y ofrece asignarlos.

Validaciones M2-M5: regenerar cada tipo de diagrama y verificar que renderiza correctamente en VS Code con la extensión PlantUML.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Plugin crece monolítico y difícil de mantener | Separación estricta skills / agents / prompts / references / templates / scripts. Cada workflow correr-aislado. |
| MD5 no detecta cambios semánticos (sólo textuales, falsea si reformatean) | Aceptable en MVP. El user siempre puede forzar regeneración con flag explícito. |
| Parser de `Build-XppInventory.ps1` tiene bugs en edge cases de sintaxis X++ | Cobertura mínima documentada: `class X extends Y`, `implements I1,I2`, `new Z()`, `static method`. Edge cases raros (macros X++, `#define`) se documentan como limitación conocida. Validar contra un módulo real en M0. |
| C4-PlantUML nivel 2 sin criterio claro de "cuándo parar" | Regla dura en `prompts/05-component-detailed.md`: exactamente un nivel de refinamiento, nunca bajar a clases (eso es nivel 4). |
| Skill externo de UML (melodic-software) puede tener sintaxis sesgada | Evaluar al inicio de M2 con un archivo X++ de prueba. Si no se adapta, escribir guía propia en `references/`. |
| User aporta insumos en PDF/Word y el skill no los lee | MVP acepta sólo Markdown/texto plano en `inputs_registered`. Fase futura: extracción multimedia. |
| PowerShell no disponible (Linux/macOS) | Los scripts `.ps1` requieren PowerShell 7+ (pwsh), disponible cross-platform. Si no está, el skill falla con mensaje claro de instalación. |
