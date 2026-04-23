# Exploración: Adaptación multi-agente de `document-xpp`

## Contexto

Este repositorio contiene el plugin `document-xpp` para Claude Code — un plugin que automatiza la generación de documentación técnica (mapa funcional, diagramas de clases, secuencia y C4) para soluciones **Dynamics 365 F&O** escritas en X++.

El plugin está 100% funcional en Claude Code (milestones M0–M5 completos, en `master`). El objetivo de esta sesión de exploración es entender **qué se necesita para que el mismo flujo de trabajo sea invocable también desde otros agentes de IA**, sin romper la integración existente con Claude Code.

**Esta es una sesión de exploración solamente. No implementes nada.**

---

## Objetivo de la exploración

Investigar una estrategia de adaptación para que el flujo `document-xpp` pueda ser ejecutado por:

| Target | CLI / Entorno |
|--------|---------------|
| **Claude Code** | `/document-xpp` (ya funciona) |
| **Gemini CLI** | `gemini` CLI + `GEMINI.md` |
| **OpenCode** | `opencode` CLI |
| **Codex CLI** | `codex` (OpenAI) |
| **KiloCode** | extensión VS Code |
| **Agentes estándar** | Cualquier agente que siga convenciones comunes (AGENTS.md, system prompts, tool calls) |

---

## Preguntas clave a responder

### 1. Capacidades comparadas

Para cada target, determiná:
- ¿Tiene sistema de plugins o skills? ¿Cuál es el entry point?
- ¿Soporta subagentes / agent spawning?
- ¿Tiene primitiva de interactividad equivalente a `AskUserQuestion`?
- ¿Puede ejecutar comandos shell (scripts Python/PowerShell)?
- ¿Qué archivos de contexto lee automáticamente? (`GEMINI.md`, `AGENTS.md`, `.cursor/rules`, etc.)
- ¿Soporta multi-turn workflows estructurados?

### 2. Inventario de portabilidad

Para cada componente del plugin actual, determiná si es:
- **Portable sin cambios** — funciona en todos los targets
- **Adaptable** — necesita reescritura pero el concepto aplica
- **Claude-específico** — no tiene equivalente en los targets

Componentes a evaluar:
- `SKILL.md` + sistema de slash commands
- `workflows/01-bootstrap.md` … `workflows/05-component-diagrams.md`
- `agents/functional-classifier.md`, `agents/uml-diagram-writer.md`, `agents/sequence-diagram-writer.md`, `agents/c4-component-writer.md`
- `prompts/01-*.md` … `prompts/05-*.md`
- `scripts/build_xpp_inventory.py`, `scripts/Compute-XppHashes.ps1`, `scripts/build_class_diagrams.py`
- `references/`, `templates/`, `tracking-schema.md`
- Sistema de persistencia (`_tracking/`, YAML de funcionalidades)

### 3. Estrategia de adaptación

Proponé UNA de estas tres estrategias (o una variante), con sus tradeoffs:

**A) Capa de compatibilidad** — Agregar archivos de entrada por target (`GEMINI.md`, `.cursor/rules`, `AGENTS.md` extendido) que referencian los mismos workflows y prompts, con instrucciones de ejecución manual para los targets que no soportan subagentes.

**B) Abstracción de workflows** — Reescribir los workflows en un formato agnóstico (ej: Markdown narrativo sin primitivas Claude-específicas), y generar adaptadores por target que mapeen las primitivas.

**C) Targets selectivos** — No apuntar a todos los targets con el mismo nivel de soporte. Definir tiers: Tier 1 (Claude Code — full support), Tier 2 (Gemini/KiloCode — adaptación razonable), Tier 3 (Codex/OpenCode — context-only).

### 4. Impacto en la estructura del repo

¿Qué cambios de estructura mínimos (archivos nuevos, carpetas, symlinks) permitirían soportar multi-agente sin tocar los archivos existentes del plugin?

---

## Archivos a leer antes de responder

Lee estos archivos en este orden para entender el estado actual:

1. `CLAUDE.md` — dispatcher general del repo
2. `plugins/document-xpp/skills/document-xpp/SKILL.md` — entry point del skill
3. `plugins/document-xpp/skills/document-xpp/workflows/01-bootstrap.md`
4. `plugins/document-xpp/skills/document-xpp/workflows/02-functional-map.md` (leer sólo Paso 1–3)
5. `plugins/document-xpp/agents/functional-classifier.md`
6. `.claude-plugin/marketplace.json`
7. `plugins/document-xpp/plugin.json`

---

## Entregable esperado

Un **informe de exploración** que incluya:

1. **Tabla de capacidades comparadas** — los targets contra las primitivas del plugin
2. **Inventario de portabilidad** — cada componente con su clasificación (portable / adaptable / Claude-específico)
3. **Estrategia recomendada** — cuál de las tres opciones (o variante) con justificación y tradeoffs
4. **Cambios estructurales mínimos** — qué archivos/carpetas nuevas necesitaría el repo
5. **Riesgos** — qué podría salir mal o qué asunciones habría que validar
6. **Preguntas abiertas** — lo que no se puede resolver sin información adicional del usuario

**No propongas implementación.** El output de esta exploración alimentará un `/sdd-new` o `/sdd-ff` en una sesión posterior.
