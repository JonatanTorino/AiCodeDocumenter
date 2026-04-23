# M0.2 — Decisión final

> **Fecha:** 2026-04-20
> **Decisor:** Jonatan Torino (jtorino@axxonconsulting.com)

---

## Decisión

**B-prime con plugin `visualization` del marketplace `melodic-software/claude-code-plugins`.**

Un solo skill cubre los 4 tipos de diagramas que necesita `document-xpp` (clases, componentes C4, contenedores C4, secuencia).

---

## Justificación

1. **Score más alto** en la matriz (6/6).
2. **MIT** — licencia compatible sin restricciones.
3. **Cero dependencias runtime** — genera `.puml` como texto; el renderizado queda a cargo del usuario (VS Code extension, plantuml.jar, etc.).
4. **Expone `plantuml-syntax` como skill de primera clase** — exactamente el soporte que `document-xpp` necesita sin reinventar sintaxis.
5. **Mismo marketplace** que ya estaba planificado en el plan v3 — la declaración en `.claude/settings.json` queda limpia (una sola URL de marketplace externo).

## Alternativas descartadas

| Alternativa | Razón de descarte |
|-------------|-------------------|
| Par separado (`bitsmuggler/c4-skill` + `SpillwaveSolutions/plantuml`) | Agrega Java + Structurizr como dependencias, licencias no declaradas. Descartado a favor de cero fricción. |
| `jovd83/PlantUML-skill` | MIT y cubre todo, pero repo más chico (15 commits), menor adopción y mantenimiento vs. marketplace melodic. Reserva como alternativa si `visualization` falla. |
| `formal-specification` | Foco en TLA+/OpenAPI/SysML, no en PlantUML puro. No cubre secuencia/clases como necesita el flujo. |
| Opción A (prerrequisito manual en README) | `visualization` cumple criterios — no hace falta caer en A. |
| Opción C (copiar al plugin local) | `visualization` cumple — C queda descartada por duplicación y pérdida de updates upstream. |

---

## Plan de prueba

**Criterio de éxito:** `visualization` genera output PlantUML equivalente o superior al que producen los prompts actuales (`02_generate_class_diagrams.md`, `03_generate_component_diagram.md`, `04_generate_container_diagram.md`, `05_generate_sequence_diagrams.md`).

**Métricas a observar en la prueba piloto (M1):**
- Calidad de la sintaxis PlantUML generada (compila sin errores en plantuml.jar).
- Fidelidad a las convenciones visuales del proyecto (colores por tipo, layers en secuencia).
- Cobertura de los 4 tipos de diagramas desde una sola skill.

**Si la prueba falla o la calidad es insuficiente:**
- **Iteración B:** reemplazar por el par especializado (`bitsmuggler/c4-skill` + `SpillwaveSolutions/plantuml`) asumiendo la fricción de Java.
- **Iteración C:** fallback a `jovd83/PlantUML-skill` (MIT, single skill, menos mantenimiento pero zero deps).

---

## Configuración a aplicar

Archivo: `.claude/settings.json` del repo (a crear en M1).

```json
{
  "extraKnownMarketplaces": {
    "melodic-software": {
      "source": {
        "type": "github",
        "repo": "melodic-software/claude-code-plugins"
      }
    }
  },
  "enabledPlugins": {
    "visualization@melodic-software": true,
    "document-xpp@aicodedocumenter-local": true
  }
}
```

> `source.type` confirmado como `github` en el `marketplace.json` del repo melodic. Requiere verificación final al momento de ejecutar M1.

---

## Pendientes derivados (para próximas sesiones)

- [ ] Actualizar `analiza-todo-el-contenido-lucky-metcalfe.md` (plan v3): reemplazar toda mención de `uml-modeling` por `visualization@melodic-software`.
- [ ] En M1, crear `.claude/settings.json` con la config de arriba.
- [ ] En M1, documentar en `plugins/document-xpp/README.md` la dependencia (incluso aunque se instale vía settings).
- [ ] Definir, en M1 o M2, el set de pruebas concreto para validar que `visualization` genera los 4 tipos de diagramas con la calidad esperada.
- [ ] Si la prueba falla, abrir M2.x de migración al par especializado.
