# document-xpp

Plugin de Claude Code que automatiza la documentación técnica de soluciones Dynamics 365 F&O escritas en X++.

## Qué hace

Guía punta a punta la generación de:

1. **Mapa funcional** — agrupa las clases del módulo por funcionalidad con criterio semántico.
2. **Diagramas de clases** — un PlantUML por grupo funcional.
3. **Diagramas de secuencia** — interactivos; el usuario elige los flujos.
4. **Diagramas de componentes C4** — nivel 1 (conceptual, global) y nivel 2 (detallado por grupo).

Soporta dos modos: documentación desde cero y actualización incremental con detección de cambios por hash MD5.

## Requisitos

- **Claude Code** (CLI, desktop o IDE extension).
- **PowerShell 7+** (`pwsh`) — los scripts de hashing e inventario son `.ps1`.
- **Plugin `visualization@melodic-software`** — dependencia declarativa para la sintaxis PlantUML/C4. Se declara en `.claude/settings.json` del repo vía `extraKnownMarketplaces` + `enabledPlugins`.

## Instalación (desde otro clon del repo)

Este plugin vive dentro de su propio marketplace local. Desde cualquier sesión de Claude Code:

```bash
/plugin marketplace add <path-al-repo-AiCodeDocumenter>
/plugin install document-xpp@aicodedocumenter-local
```

Verificá que `/document-xpp` aparezca en el autocomplete.

## Uso

```bash
/document-xpp
```

El skill pide:

- Ubicación de la carpeta `XppSource/` con los archivos `.xpp`.
- Directorio del workspace de documentación (dónde caerán los entregables).
- Tipo de sesión: `nuevo`, `actualizar`, `agregar-independiente`, `agregar-relacionado`.

El resto es conversacional — el skill orquesta los workflows por fase y pregunta cuando necesita decisiones humanas.

## Estructura del plugin

```
plugins/document-xpp/
  .claude-plugin/plugin.json
  skills/document-xpp/
    SKILL.md                  # entry point
    workflows/                # un workflow por fase
    prompts/                  # prompts atómicos invocados desde workflows
    references/               # exclusion-list, tracking-schema, visual-conventions
    templates/                # YAML y CSV templates
    scripts/                  # PowerShell: hashing + parseo X++
  agents/
    functional-classifier.md  # Fase 2: agrupa clases por funcionalidad
    diagram-writer.md         # Fases 3–5: genera .puml
```

## Estado

- **M0** — investigación y prototipos (cerrado).
- **M1** — `nuevo` + detección de workspace existente con diff de hashes (en curso).
- **M2** — diagramas de clases.
- **M3** — diagramas de componentes C4.
- **M4** — diagramas de secuencia interactivos.
- **M5** — modos `actualizar` / `agregar-*` completos.

Ver `analiza-todo-el-contenido-lucky-metcalfe.md` en la raíz del repo para el plan completo.

## Licencia

MIT.
