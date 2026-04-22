# CLAUDE.md

Guía de contexto para agentes de IA (Claude, Gemini, Grok, Copilot, Cursor, etc.) trabajando en este repositorio. Si sos humano, empezá por `plugins/document-xpp/README.md`.

Este archivo es un **dispatcher**: te dice dónde está cada cosa y por qué. El detalle vive en los docs referenciados — no lo dupliques acá.

---

## Qué es este repo

`AiCodeDocumenter` es el repositorio de desarrollo del Claude Code plugin **`document-xpp`**, que automatiza la generación de documentación técnica (mapa funcional + diagramas de clases / secuencia / C4) para soluciones **Dynamics 365 F&O** escritas en X++.

El repo **es** el marketplace local desde el cual se instala el plugin. No es una app tradicional: no tiene build propio. Los "entregables" son prompts, workflows, agentes y scripts que orquesta Claude Code.

## Estado actual

- **M1 mergeado** en `master` (merge commit `f6a2db7`, 2026-04-21). Cubre Fase 1 (bootstrap) y Fase 2 (mapa funcional) end-to-end en modo `nuevo`.
- **M1.5 en curso** — limpieza de docs de contexto para IAs + `visual-conventions.md`.
- **M2 en planificación** — diagramas de clases MVP con re-etiquetado semántico de relaciones.
- Plan completo de milestones: `analiza-todo-el-contenido-lucky-metcalfe.md`.

## Dónde está cada cosa

### Tier 1 — Lectura obligatoria si vas a tocar el plugin

| Archivo | Por qué |
|---|---|
| `plugins/document-xpp/README.md` | Propósito del plugin, requisitos, instalación y uso end-to-end |
| `plugins/document-xpp/skills/document-xpp/SKILL.md` | Entry point del skill, tabla de fases, qué NO hacer |
| `plugins/document-xpp/skills/document-xpp/references/tracking-schema.md` | **Contrato de datos** (manifest / hashes / inventory / dependencies / funcionalidades YAML). Cualquier cambio acá impacta parser + agent + workflows |
| `plugins/document-xpp/skills/document-xpp/references/exclusion-list.md` | Clases del framework D365 que el classifier debe ignorar como ruido técnico |

### Tier 2 — Lectura específica según la fase que toques

| Si trabajás en... | Leé |
|---|---|
| Fase 1 (bootstrap) | `plugins/document-xpp/skills/document-xpp/workflows/01-bootstrap.md` |
| Fase 2 (mapa funcional) | `workflows/02-functional-map.md` + `agents/functional-classifier.md` + `prompts/01-*.md` + `prompts/02-*.md` |
| Parser X++ / AxEnum / AxEdt | `scripts/build_xpp_inventory.py` (Python ≥ 3.10, stdlib-only; docstring documenta limitaciones conocidas) |
| Hashing MD5 | `scripts/Compute-XppHashes.ps1` (PowerShell 5.1+) |
| Estilo visual de diagramas | `plugins/document-xpp/skills/document-xpp/references/visual-conventions.md` |

### Tier 3 — Contexto histórico (entender POR QUÉ algo se hizo así)

| Archivo | Usalo cuando... |
|---|---|
| `M0.2-investigacion-plugin-uml/03-decision.md` | Te preguntás por qué se adoptó `visualization@melodic-software` y no CLI directo a PlantUML |
| `plugins/document-xpp/.validation/m1-workspace-sample/` | Necesitás ver output real del flujo M1 contra un módulo D365 concreto (48 clases, 135 deps, 7 grupos). Sirve de *regression baseline* |
| `discontinued/` | Querés entender el flujo legacy pre-plugin (prompts numerados + LLM externo manual). **NO consumir como fuente de verdad** — es archivo histórico |
| `analiza-todo-el-contenido-lucky-metcalfe.md` | Buscás el plan maestro de milestones M0–M5 |

### Tier 4 — Memoria persistente (si tu runtime la soporta)

- **Engram**: `mem_search` con topic keys bajo `document-xpp/*`. Ej: `document-xpp/m1-pr` tiene el post-mortem de M1.
- **Auto-memory de Claude Code**: `~/.claude/projects/<proyecto>/memory/MEMORY.md` (índice) — persiste entre sesiones del mismo usuario.

## Inputs del código fuente

- El flujo consume `.xpp`. Si sólo tenés `.xml` de AOT, hay un extractor en el repo hermano `AiCodeReviewer/xml-xpp-parser/Invoke-AxSourceExtraction.ps1` que los convierte.
- Convención de nombres X++ en D365: `[Prefijo][Infijo_Funcional][Nombre].xpp` (ej: `AxnLicSubscriptionService.xpp`). El classifier usa esta convención para clustering.

## Qué NO hacer

- **No leas ni reimplementes nada de `discontinued/`.** Es el flujo viejo. Si algo no está cubierto por el plugin actual, reportalo como gap — no lo recicles.
- **No dupliques contenido del README del plugin en este archivo.** Este CLAUDE.md es dispatcher, no manual.
- **No inventes CSVs o schemas.** `tracking-schema.md` es el contrato — cualquier cambio pasa por actualizar el schema + parser + agent + workflows en el **mismo commit**.
- **No commitees** `*.xpp`, `.venv/`, `__pycache__/`, ni el `hashes.csv` de validación (mtime-volátil). El `.gitignore` cubre los primeros; el último es exclusión intencional documentada en `.validation/.../README.md`.

## Convenciones operativas

- **Commits**: conventional commits (`feat(scope): `, `docs: `, `chore: `, `fix(scope): `). El cuerpo explica el **por qué**, no el qué.
- **Sin `Co-Authored-By`** ni atribución a IA en commits. Política del repo.
- **Un PR por milestone**. No diferir. Flujo: Issue → rama → PR → merge → rama siguiente *stacked sobre master fresco* (no sobre la rama anterior).
- **Validación golden**: al tocar el parser o el classifier, regenerar `plugins/document-xpp/.validation/m1-workspace-sample/` y diffear contra la versión commiteada. `hashes.csv` se excluye del diff.

## Protocolo de mantenimiento de este archivo

Actualizá este `CLAUDE.md` cuando:

- Se agregue una nueva fase / workflow al plugin → extender Tier 2.
- Un archivo de Tier 1 cambie de ubicación o nombre.
- Cambie el estado del milestone vigente (línea de "Estado actual").

Si movés archivos, actualizá los pointers acá. **`AGENTS.md` es un symlink a este archivo** — un cambio cubre a cualquier IA que prefiera esa convención (Cursor, Gemini CLI, etc.).
