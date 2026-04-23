# M0.2 — Plan de investigación: dependencia externa UML/PlantUML

> **Estado:** ✅ COMPLETADO — 2026-04-20
> **Decisión:** B-prime con plugin `visualization` del marketplace `melodic-software/claude-code-plugins`.
> **Detalle completo:** ver carpeta [`M0.2-investigacion-plugin-uml/`](./M0.2-investigacion-plugin-uml/) (plan + resultado + decisión).
> **Desbloquea:** M1 (creación del plugin `document-xpp`).
>
> _Contenido histórico abajo preservado como referencia del plan original._

---

> **Estado original (pre-cierre):** pendiente de ejecución en otra sesión.
> **Bloquea:** cierre de M0 y arranque de M1 (creación del plugin).
> **Sesión principal:** continuará con M0.3 (prototipo `Build-XppInventory.ps1`) mientras esto se resuelve en paralelo.

---

## 1. Contexto

El plan v3 (`analiza-todo-el-contenido-lucky-metcalfe.md`) asume que existe un plugin externo llamado `uml-modeling` en el marketplace `melodic-software/claude-code-plugins`, del que `document-xpp` dependería para generar diagramas PlantUML (clases, componentes C4, secuencia).

**Verificación inicial (ya realizada):** el repo `melodic-software/claude-code-plugins` existe (58★, 35 plugins) pero **NO contiene un plugin llamado `uml-modeling`**. El plan v3 arrastra un nombre incorrecto.

Candidatos reales detectados en ese marketplace:
- `formal-specification` — UML/SysML, TLA+, OpenAPI/AsyncAPI, state machines.
- `visualization` — genéricamente orientado a visualización.

**Hallazgo técnico adicional:** el `plugin.json` de Claude Code **NO soporta un campo `dependencies`**. Los únicos campos oficiales son `name`, `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`. Esto invalida la Opción B literal del plan.

La alternativa equivalente ("B-prime") es declarar la dependencia a nivel de settings del proyecto vía `extraKnownMarketplaces` + `enabledPlugins` en `.claude/settings.json` — lo que sí se versiona en git y se aplica a todo el equipo al clonar.

---

## 2. Opciones en orden de preferencia

| Orden | Opción | Descripción | Ventaja | Costo |
|-------|--------|-------------|---------|-------|
| **1** | **B-prime** | `.claude/settings.json` en el repo declara `extraKnownMarketplaces` (URL del marketplace externo) + `enabledPlugins` (el plugin UML) | Dependencia declarativa, se instala sola al clonar | Requiere que el plugin externo exista y sea útil |
| **2** | **A (fallback)** | Documentar el plugin UML como prerrequisito en el README del plugin + instrucciones de instalación manual | Simple, sin acoplamiento técnico | Fricción de onboarding |
| **3** | **C (último recurso)** | Extraer/copiar el contenido relevante del plugin externo dentro de `plugins/document-xpp/skills/` | Autosuficiente | Duplica código, pierde updates upstream, potenciales temas de licencia |

> **Regla del usuario:** *"prefiero la opción A como fallback antes que la C"*. C solo si A también falla.

---

## 3. Tareas concretas de la investigación

### 3.1. Inspeccionar los candidatos

Usar `WebFetch` sobre estas URLs y revisar qué expone cada plugin:

- `https://github.com/melodic-software/claude-code-plugins/tree/main/plugins/formal-specification`
- `https://github.com/melodic-software/claude-code-plugins/tree/main/plugins/visualization`
- `https://github.com/melodic-software/claude-code-plugins/blob/main/.claude-plugin/marketplace.json` (para ver la entrada oficial del plugin: `name`, `source`, versión)

Para cada uno, documentar:
- Nombre exacto del plugin (campo `name` en `plugin.json` o `marketplace.json`).
- Skills/agents/commands que expone.
- Si incluye helpers/templates específicos de **PlantUML**.
- Si cubre los tres tipos de diagramas que necesita `document-xpp`: **clases**, **componentes C4**, **secuencia**.
- Licencia.
- Frecuencia de actualización (último commit).

### 3.2. Criterios de evaluación

Un candidato califica para **B-prime** si cumple al menos:

- [ ] Expone sintaxis/templates PlantUML para **diagramas de clases** (equivalente a lo que hoy produce `02_generate_class_diagrams.md`).
- [ ] Expone sintaxis/templates PlantUML para **diagramas de secuencia** con layers (equivalente a `05_generate_sequence_diagrams.md`).
- [ ] Cubre **C4 Component/Container** (o al menos una base que permita agregarlo desde `document-xpp`).
- [ ] Licencia compatible (MIT, Apache, BSD o similar permisivo).
- [ ] Mantiene versionado semántico / commits recientes.

Si cumple 3 de 4 → B-prime.
Si cumple solo 1-2 → A con instrucciones manuales.
Si no cumple ninguno → buscar marketplace alternativo (siguiente paso).

### 3.3. Si ningún candidato califica — búsqueda alternativa

Buscar en este orden:
1. `site:github.com claude-code plugin plantuml` (web search).
2. Marketplaces listados en la documentación oficial: `https://docs.claude.com/en/docs/claude-code/plugins-marketplaces`.
3. Repos de la comunidad (awesome-claude-code, etc.).

Si no aparece nada dedicado → ir directo a **Opción A**: documentar PlantUML como herramienta externa (el usuario instala Java + plantuml.jar o usa VS Code extension). Aclarar en el README que el plugin genera `.puml` y el renderizado queda a cargo del usuario.

---

## 4. Árbol de decisión final

```
¿formal-specification cumple criterios?
├─ SÍ → B-prime con formal-specification
└─ NO → ¿visualization cumple criterios?
        ├─ SÍ → B-prime con visualization
        └─ NO → ¿existe otro plugin PlantUML en la comunidad?
                ├─ SÍ → B-prime con ese plugin
                └─ NO → Opción A: PlantUML como prerrequisito externo en README
                        (C queda descartada salvo decisión explícita del usuario)
```

---

## 5. Ejemplo concreto de B-prime (referencia técnica)

Si B-prime queda elegido, así quedaría `.claude/settings.json` del repo:

```json
{
  "extraKnownMarketplaces": {
    "melodic-plugins": {
      "source": {
        "type": "github",
        "repo": "melodic-software/claude-code-plugins"
      }
    }
  },
  "enabledPlugins": {
    "<nombre-real-del-plugin>@melodic-plugins": true,
    "document-xpp@<marketplace-local>": true
  }
}
```

> El campo `source.type` puede ser `github`, `url` o `git`. Verificar durante la investigación cuál acepta el marketplace externo (leer su `marketplace.json` oficial).

Esto logra el efecto de "dependencia declarativa": al clonar el repo y abrirlo con Claude Code, el plugin externo se descubre e instala automáticamente.

---

## 6. Pendientes post-investigación

Al cerrar esta investigación, actualizar:

1. **Plan v3** (`analiza-todo-el-contenido-lucky-metcalfe.md`):
   - Reemplazar toda mención de `uml-modeling` por el plugin real elegido.
   - Si se elige A, eliminar la sección B/B-prime y agregar la sección de prerrequisitos.
2. **Engram** — topic key `architecture/aicodedocumenter-mvp`:
   - Guardar la decisión final (B-prime/A) con `mem_save` (tipo `decision`).
   - Incluir criterios evaluados y razón del descarte de las otras opciones.
3. **README del plugin** (`plugins/document-xpp/README.md`, cuando se cree en M1):
   - Sección de instalación acorde a la opción elegida.
4. **Este archivo** (`M0.2-investigacion-plugin-uml.md`):
   - Marcar como COMPLETADO al inicio, con fecha y plugin elegido.

---

## 7. Definition of Done

- [ ] `formal-specification` y `visualization` inspeccionados con `WebFetch`.
- [ ] Matriz de criterios completada para cada candidato.
- [ ] Decisión tomada: B-prime / A (+ plugin específico si B-prime).
- [ ] Plan v3 actualizado (nombre real del plugin o sección A).
- [ ] Engram actualizado con `mem_save` tipo `decision`.
- [ ] Este archivo marcado COMPLETADO con resumen de la decisión.

---

## 8. Notas de continuidad

- La sesión principal **sigue adelante con M0.3** (prototipo `Build-XppInventory.ps1`) mientras esto se resuelve.
- M1 (creación de archivos del plugin) **puede arrancar igual** — solo queda pendiente la sección de instalación/dependencia UML, que se completa al cerrar este documento.
- El `marketplace.json` local (`.claude-plugin/marketplace.json`) se puede crear desde ya: no depende de esta investigación.
