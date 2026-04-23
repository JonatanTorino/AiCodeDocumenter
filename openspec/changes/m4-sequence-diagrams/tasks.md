# Tasks: M4 — Diagramas de Secuencia

> Paths relativos a `plugins/document-xpp/`.
> Fase 1 y 2 pueden ejecutarse en paralelo. Fase 3 depende de Fase 2. Fase 4 depende de Fase 3. Fase 5 depende de todas.

---

## Fase 1: Fundamentos (template + convenciones)

- [x] 1.1 `skills/document-xpp/references/visual-conventions.md` — agregar sección `## Sequence Diagrams` al final: 3-layer structure (Presentation/Business Logic/Data), paleta de colores por capa (`<<Form>>` violeta, `<<Table>>` verde, `<<External>>` gris), reglas de ruido (no parm*, no new triviales), autonumber + activate/deactivate obligatorios
- [x] 1.2 Crear `skills/document-xpp/templates/sequence-diagram.puml.tpl` — skeleton con: `@startuml {{slug}}-{{flow_slug}}`, `!theme plain`, `autonumber`, skinparams por capa, `title {{flow_name}}`, `actor "Usuario" as User`, `box "Presentation"`, `box "Business Logic"`, `box "Data"`, placeholder de flujo, `@enduml`

---

## Fase 2: Agente

- [x] 2.1 Crear `agents/sequence-diagram-writer.md` — persona (arquitecto D365, behavioral modeling), dos modos explícitos (`discover`: lee .xpp → candidatos JSON sin escribir archivos; `generate`: escribe .puml), inputs del orquestador (`mode`, `funcionalidad_yaml_path`, `xpp_root`, `workspace_path`, `template_path`, `prompt_path`, `visual_conventions_path`, más `flow_name`+`entry_point`+`puml_output_path` en mode=generate), archivos que lee, contrato JSON para cada modo, reglas: qué NO hacer (no parm*, no new triviales, no bajar al level de variables locales)

---

## Fase 3: Prompt + Workflow

- [x] 3.1 Crear `skills/document-xpp/prompts/04-sequence-diagram.md` — procedimiento paso a paso: (1) cargar template + visual-conventions sección sequence; (2) leer funcionalidad YAML → listar clases del grupo; (3) si mode=discover: leer .xpp, identificar entry points, proponer flujos de negocio, armar JSON de candidatos; (4) si mode=generate: leer .xpp del entry point + clases participantes, trazar llamadas en 3 capas, omitir ruido, rellenar template, escribir .puml, armar JSON de respuesta
- [x] 3.2 Crear `skills/document-xpp/workflows/04-sequence-diagrams.md` — 7 pasos: (1) verificar funcionalidades en workspace; (2) seleccionar grupo funcional (AskUserQuestion si hay múltiples); (3) leer manifest.yaml → obtener xpp_root; (4) invocar agente mode=discover → candidatos; (5) AskUserQuestion con candidatos; (6) por cada flujo elegido: invocar agente mode=generate → validación humana (Aceptar/Ajustar/Rehacer) → actualizar YAML de tracking; (7) resumen final

---

## Fase 4: Actualizaciones

- [x] 4.1 `skills/document-xpp/SKILL.md` — fila Fase 4: reemplazar `"Diagramas de secuencia interactivos | M4 — no disponible todavía"` por `"Diagramas de secuencia interactivos | Siempre después de 2 si el usuario quiere diagramas de secuencia"`; actualizar estado en comentario final del archivo
- [x] 4.2 `skills/document-xpp/workflows/03-class-diagrams.md` — último paso: next-phase apunta a `04-sequence-diagrams.md` (actualmente apunta a Fase 5)
- [x] 4.3 `CLAUDE.md` — línea de estado: M3 mergeado, M4 en revisión / mergeado según el momento

---

## Fase 5: Verificación

- [x] 5.1 `grep -r "no disponible todavía" plugins/` — debe devolver 0 resultados (Fase 4 habilitada)
- [x] 5.2 Verificar que `sequence-diagram.puml.tpl` contiene `autonumber`, los 3 `box`, y `title`
- [x] 5.3 Verificar que `04-sequence-diagrams.md` referencia al agente `sequence-diagram-writer` con los inputs correctos (`mode`, `funcionalidad_yaml_path`, `xpp_root`)
- [ ] 5.4 Ejecutar Workflow 04 contra workspace golden con Fases 1-3 completas; verificar que `conceptual.puml` generado renderiza en VS Code con `visualization@melodic-software`
