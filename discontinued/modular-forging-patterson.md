# Plan: Skill `ax-doc` — Documentación Técnica Automatizada D365 F&O

## Contexto

El directorio `AiCodeDocumenter/` contiene un flujo de 6 prompts secuenciales que se ejecutan **manualmente** en LLMs externos (Gemini, Grok, Claude) para transformar código X++ en documentación técnica y diagramas PlantUML. El flujo funciona (3 tests exitosos con diferentes LLMs), pero es frágil, manual, y no permite generar diagramas individuales.

El objetivo es crear un **skill para Claude Code** que orqueste este flujo internamente, permita generar **un diagrama a la vez**, gestione estado, y filtre inteligentemente los archivos .xpp por grupo funcional.

---

## 1. Debilidades del Flujo Actual (Priorizadas)

### Críticas (el skill las resuelve directamente)

| ID | Debilidad | Impacto |
|----|-----------|---------|
| D1 | **Flujo completamente manual**: copiar prompts entre LLMs externos, subir archivos, pasar outputs | Fricción alta, error humano |
| D2 | **Sesión frágil**: prompts dicen "mantén la sesión abierta" entre pasos | Pérdida de contexto = reinicio total |
| D4 | **Generación masiva obligatoria**: Paso 3 genera TODOS los diagramas de clase de golpe | Sobrecarga de contexto, calidad degradada |
| D5 | **Sin filtrado de archivos**: Se suben 53 .xpp para un grupo de 7 clases | Contexto desperdiciado, calidad menor |
| D6 | **Sin validación de pre-requisitos**: nada verifica que existan artefactos previos | Errores silenciosos |

### Altas (mejora significativa)

| ID | Debilidad | Solución |
|----|-----------|----------|
| D3 | Sin estado persistido | Archivo JSON de estado que trackea pasos completados |
| D7 | Sin validación de output PlantUML | Verificación básica de sintaxis |
| D8 | Inconsistencia entre LLMs (Grok falló Paso 1) | Se elimina: Claude Code es el único LLM |
| D11 | Conversión XML→XPP separada | El skill puede invocar `Invoke-AxSourceExtraction.ps1` |

### Medias (limitación inherente o fuera de scope)

| ID | Debilidad | Nota |
|----|-----------|------|
| D9 | Paso 6 (secuencia) necesita doc funcional externa | El skill la acepta como parámetro; no puede generarla |
| D10 | 6 archivos Staging fallan en conversión XML→XPP | Requiere fix en scripts PowerShell, no en el skill |

---

## 2. Mejoras Sustanciales Propuestas

### M1: Diagrama por petición (granularidad)
En lugar de generar todos los diagramas de clase a la vez, el usuario pide uno:
`/ax-doc class "Checker"` → Solo genera el diagrama del grupo "Checker".
Aplica también a secuencias: `/ax-doc sequence "Proceso de Facturación"`.

### M2: Filtrado inteligente de archivos .xpp
Para generar el diagrama del grupo "Checker" (7 clases), el skill:
1. Lee el `functional_map.md` y extrae las clases del grupo + sus rutas
2. Lee solo esos 7 archivos .xpp (no los 53)
3. Las referencias internas de otros grupos se marcan como `<<External>>` sin leer su .xpp

### M3: Estado persistido
**Problema que resuelve:** El flujo de documentación es inherentemente multi-sesión. Generar el functional map de un proyecto con 50+ clases puede tomar toda una conversación, y los diagramas de clase se generan de a uno por grupo en sesiones separadas. Sin estado, el usuario no sabe qué pasos están completos, qué grupos ya tienen diagrama, y arriesga re-generar outputs que ya existen o pisar trabajo previo. El archivo de estado es la "memoria entre sesiones": permite retomar el flujo desde donde se dejó y habilita la validación automática de pre-requisitos.

**Situación práctica:** Generaste el functional map el lunes. El martes querés generar solo el diagrama del grupo "Checker" sin rehacer el flujo completo. El estado confirma que el map ya existe, dónde está, y el skill salta directo al Paso 2 sin preguntas.

**Decisión de diseño:** Si el valor no justifica la complejidad en la práctica, esta mejora puede postergarse a una v1.1. Los pasos 0-5 funcionan sin ella; el costo es tener que re-verificar manualmente qué outputs ya existen.

Archivo `.ax-doc-state.json` en la raíz del proyecto que trackea:
- Nombre del producto, ruta de fuentes .xpp
- Estado de cada paso (pending/completed/partial)
- Para diagramas de clase: estado por grupo individual
- Para secuencias: estado por escenario individual
- Rutas de outputs generados, timestamps

### M4: Validación automática de pre-requisitos
Antes de cada paso, verificar que los artefactos previos existen:
- `class` requiere `functional_map.md` → si no existe, informar al usuario
- `map` requiere archivo de grupos → si no existe, ofrecer ejecutar `groups`

### M5: Ejecución nativa vía herramienta agente
Al implementarse como un skill, la herramienta agente que lo ejecute (Claude Code, Cursor, Kilo Code u otra compatible) lee los archivos .xpp del filesystem, aplica la lógica de análisis internamente, y escribe los outputs directamente. Elimina la dependencia de sesiones en LLMs externos y el copiado manual de prompts entre herramientas.

### M6: Integración con xml-xpp-parser
El comando `convert` invoca `Invoke-AxSourceExtraction.ps1` vía Bash para convertir XML→XPP. La ruta canónica del script es:
`C:\Repos\AxxonPractica\AxxonPracticaDev\AiCodeReviewer\xml-xpp-parser\Invoke-AxSourceExtraction.ps1`

**Comportamiento importante:** Cada ejecución de `convert` elimina los archivos `.xpp` existentes y los regenera desde cero. Por eso, cualquier indexación de archivos `.xpp` debe ocurrir después de `convert`, no antes ni durante `init`.

---

## 3. Arquitectura del Skill

### 3.1 Estructura de archivos a crear

```
C:\Users\jtorino\.claude\skills\ax-doc\
├── SKILL.md                              # Instrucciones principales (~450 líneas)
├── references\
│   ├── exclusion_list.md                  # Copia de Prompts/01_exclusion_list.md
│   ├── plantuml_styles.md                 # Estilos PlantUML consolidados de prompts 02-05
│   ├── functional_groups_guide.md         # Reglas de identificación de grupos (del prompt 00)
│   ├── c4_templates.md                    # Templates C4 componentes + contenedores (prompts 03-04)
│   └── sequence_templates.md              # Template secuencia con 3 capas (prompt 05)
└── scripts\
    └── README.md                          # Ruta canónica: AiCodeReviewer\xml-xpp-parser\Invoke-AxSourceExtraction.ps1
```

### 3.2 Estructura esperada del proyecto del usuario

```
{ProjectRoot}/                            # Ej: AiCodeDocumenter/
├── xpp/                                  # Archivos .xpp (fuente)
│   └── {Modelo}/{Nombre}/AxClass/*.xpp
├── Output/
│   ├── {Producto}_{fecha}.md             # Paso 0: grupos
│   ├── {Producto}_functional_map.md      # Paso 1: mapa funcional
│   └── Diagrams/
│       ├── Class/{Grupo}.puml            # Paso 2: diagramas de clase
│       ├── C4/
│       │   ├── {Prod}_component_diagram.puml          # Paso 3
│       │   └── {Prod}_container_diagram.puml          # Paso 4
│       └── Sequence/{Escenario}.puml     # Paso 5
└── .ax-doc-state.json                    # Estado del flujo
```

---

## 4. Comandos del Skill

| Comando | Descripción | Pre-requisitos |
|---------|-------------|----------------|
| `/ax-doc init <ruta_metadata_xml> <nombre_producto>` | Configura el proyecto: define nombre y rutas de fuentes XML y salida. No requiere `.xpp` previos | Ninguno |
| `/ax-doc convert` | Convierte XML→XPP (elimina `.xpp` previos, regenera, re-indexa). Verifica presencia de `.dbml` y advierte si falta | `init` completado + script `Invoke-AxSourceExtraction.ps1` accesible |
| `/ax-doc status` | Muestra estado actual del flujo | Estado existente |
| `/ax-doc groups` | Paso 0: identifica grupos funcionales | `convert` completado + `.dbml` presente |
| `/ax-doc map` | Paso 1: genera functional map completo | Paso 0 completado |
| `/ax-doc map "Grupo1" "Grupo2"` | Paso 1 filtrado: solo grupos indicados | Paso 0 completado |
| `/ax-doc class "NombreGrupo"` | Paso 2: diagrama de clases de UN grupo | Paso 1 completado |
| `/ax-doc class --all` | Paso 2: diagrama de clases de TODOS los grupos (uno por uno) | Paso 1 completado |
| `/ax-doc component [ruta_doc_alcance]` | Paso 3: diagrama C4 de componentes. Doc funcional/alcance opcional para enriquecer etiquetas | Paso 1 completado |
| `/ax-doc container [ruta_doc_alcance]` | Paso 4: diagrama C4 de contenedores. Doc funcional/alcance opcional para enriquecer etiquetas | Paso 1 completado |
| `/ax-doc sequence <ruta_doc_funcional>` | Paso 5: diagramas de secuencia | Paso 1 + doc funcional |

> **Prerequisito post-conversión:** Antes de habilitar cualquier paso de documentación (`groups` en adelante), debe existir un archivo `.dbml` que represente el modelo de datos del proyecto. El comando `convert` verifica su presencia y bloquea el flujo con un mensaje claro si no está disponible.

---

## 5. Diseño del SKILL.md — Secciones Clave

### Sección 1: Frontmatter
```yaml
name: ax-doc
description: |
  Automated technical documentation for Dynamics 365 F&O X++ solutions.
  Generates functional maps, UML class diagrams, C4 component/container diagrams,
  and sequence diagrams from X++ source code. Use when the user says "ax-doc",
  "document X++ code", "generate class diagram for D365", "create functional map",
  "PlantUML from X++", "documentar código X++", "generar diagrama", or any request
  to produce technical documentation from Dynamics 365 source code.
version: 1.0.0
tools: [Read, Write, Edit, Glob, Grep, Bash]
```

### Sección 2: Rol y Contexto
Claude actúa como Arquitecto de Soluciones D365 F&O. Explica el flujo de 6 pasos. Referencia los archivos en `references/` como fuentes de verdad para exclusiones, estilos y templates.

### Sección 3: Inicialización (`init`)
1. Glob `**/*.xpp` en la ruta proporcionada
2. Contar archivos por tipo (AxClass, AxTable, AxForm)
3. Crear `.ax-doc-state.json` con producto, rutas, conteo
4. Reportar resumen al usuario

### Sección 4: Detección de Estado y Pre-requisitos
Antes de cada comando:
1. Leer `.ax-doc-state.json` (si no existe → pedir `init`)
2. Para `groups` y pasos posteriores: verificar que existe el archivo `.dbml` definido en el estado. Si no existe, bloquear con mensaje: *"Falta el archivo .dbml del modelo de datos. Generalo y registrá su ruta antes de continuar."*
3. Verificar pre-requisitos del paso correspondiente (pasos anteriores completados, archivos de output existentes)
4. Si faltan, informar qué ejecutar primero

### Sección 5: Paso 0 — Identificar Grupos Funcionales
- Leer `references/functional_groups_guide.md` para las reglas de detección
- Glob los archivos .xpp y analizar nombres (prefijos, infijos)
- Proponer grupos funcionales con formato `Group: [Nombre] | [Patrones]`
- Escribir output en `Output/{Producto}_{fecha}.md`
- Actualizar estado

### Sección 6: Paso 1 — Generar Functional Map
- Leer el archivo de grupos del Paso 0
- Leer `references/exclusion_list.md` para filtrar dependencias
- Leer TODOS los .xpp (este paso necesita el código completo)
- Para cada archivo: clasificar en grupo, mapear dependencias internas/externas
- Generar tabla Markdown con formato: `Clase | Referencias Internas | Referencias Externas`
- Escribir `Output/{Producto}_functional_map.md`
- Actualizar estado con lista de grupos y conteo de clases

### Sección 7: Paso 2 — Diagrama de Clases (POR GRUPO)
**Esta es la sección más crítica del skill.**
- Leer `references/plantuml_styles.md` para estilos de clase
- **Filtrado inteligente**: parsear el functional map, extraer solo las clases del grupo solicitado
- Leer solo los .xpp de esas clases (no todos)
- Analizar métodos públicos, atributos, herencia
- Aplicar reglas de estilo: Internal (#F9F9F9), Table (#E8F5E9), External (#37BEF3)
- Si tabla tiene >10 campos → mostrar 10 principales + `... (more)`
- Relaciones semánticas (no genéricas): `extiende`, `implementa`, `valida`, `persiste`
- Escribir `Output/Diagrams/Class/{NombreGrupo}.puml`
- Validar PlantUML básico y actualizar estado

### Sección 8: Pasos 3-4 — Diagramas C4
- Leer `references/c4_templates.md` para templates
- Si se proveyó `[ruta_doc_alcance]`, leerla para enriquecer etiquetas y descripciones
- Leer functional map completo (no los .xpp)
- Componentes: cada grupo funcional → un Component C4
- Contenedores: AOS + AxDB obligatorios + detección de integraciones externas por keywords
- Escribir .puml en `Output/Diagrams/C4/` (carpeta unificada para componentes y contenedores)

### Sección 9: Paso 5 — Diagramas de Secuencia
- Leer `references/sequence_templates.md`
- Requiere doc funcional como input adicional
- Identificar escenarios (Happy Path), mapear contra código
- 3 capas: Presentation (Forms), Business Logic (Classes), Data Layer (Tables)
- Ignorar parmMethods, new, getters/setters
- Un .puml por escenario

### Sección 10: Validaciones de Output
Después de generar cada .puml:
1. Verificar `@startuml` al inicio y `@enduml` al final
2. Verificar que no hay packages/clases vacíos
3. Para C4: verificar `!include` de librería C4
4. Para secuencias: verificar `autonumber`

---

## 6. Estrategia de Filtrado de Archivos .xpp

### Algoritmo (Paso 2: class diagram por grupo)

```
1. Leer {Producto}_functional_map.md
2. Encontrar la sección ### {NombreGrupo}
3. Parsear la tabla Markdown de ese grupo
4. Para cada fila:
   a. Extraer nombre de clase y ruta del link [Clase](ruta)
   b. Extraer referencias internas (también con rutas)
5. Construir set de archivos .xpp a leer:
   - Directos: clases listadas en la columna "Clase" del grupo
   - Indirectos: referencias internas de OTROS grupos → NO se leen, se marcan <<External>>
6. Leer solo los archivos directos con Read
7. Las referencias externas (columna "Referencias Externas") → solo nombre, sin leer
```

### Ejemplo: Grupo "Checker" (del Test1)
- **Directos** (7 archivos a leer): AxnLicExtensionChecker, AxnLicFeatureChecker, AxnLicSubscriptionChecker, AxnLicSubscriptionChecker_Extension, AxnLicMetadataChecker, AxnLicMetadataCheckerContract, AxnLicMetadataCheckerTestJob
- **Internos de otros grupos** (marcados External, NO se leen): AxnLicSubscriptionExtension, AxnLicSubscription, AxnLicUser, AxnLicParameters, etc.
- **Externos** (solo nombre): DateTimeUtil, Microsoft.Dynamics.AX.Metadata, Args

**Reducción**: de 53 archivos a 7 (87% menos contexto).

---

## 7. Formato del Archivo de Estado `.ax-doc-state.json`

```json
{
  "version": "1.0",
  "product_name": "License",
  "xpp_source_path": "./Output/xpp/Axxon365LicenseManagement/...",
  "created_at": "2026-04-03T10:00:00Z",
  "updated_at": "2026-04-03T12:30:00Z",
  "xpp_file_index": { "total": 53, "AxClass": 34, "AxTable": 14, "AxForm": 5 },
  "steps": {
    "groups": { "status": "completed", "output_file": "Output/License_20260403.md", "groups": ["Checker", "..."] },
    "functional_map": { "status": "completed", "output_file": "Output/License_functional_map.md" },
    "class_diagrams": {
      "Checker": { "status": "completed", "output_file": "Output/Diagrams/Class/Checker.puml" },
      "Consulta de Web Service": { "status": "pending" }
    },
    "component_diagram": { "status": "pending", "output_file": "Output/Diagrams/C4/{Prod}_component_diagram.puml" },
    "container_diagram": { "status": "pending", "output_file": "Output/Diagrams/C4/{Prod}_container_diagram.puml" },
    "dbml_path": "Output/{Prod}.dbml",
    "sequence_diagrams": {}
  }
}
```

---

## 8. Secuencia de Implementación

### Fase 1: Esqueleto (mínimo viable)
1. Crear `~/.claude/skills/ax-doc/SKILL.md` con frontmatter + `init` + `status`
2. Crear `references/exclusion_list.md` (copia de `Prompts/01_exclusion_list.md`)
3. Implementar lógica de estado JSON
4. **Verificación**: `/ax-doc init` sobre los .xpp existentes en `Output/xpp/`

### Fase 2: Fundamentos (Pasos 0-1)
5. Crear `references/functional_groups_guide.md`
6. Implementar `groups` y `map` en SKILL.md
7. **Verificación**: comparar output con `Tests/Test1/Output/License_functional_map.md`

### Fase 3: Diagramas de clase (paso más complejo)
8. Crear `references/plantuml_styles.md`
9. Implementar `class "NombreGrupo"` con filtrado inteligente
10. **Verificación**: generar "Checker" y comparar con `Tests/Test1/Output/Diagrams/Class/Checker.puml`

### Fase 4: Diagramas C4
11. Crear `references/c4_templates.md`
12. Implementar `component` y `container`
13. **Verificación**: comparar con outputs de Test1

### Fase 5: Secuencias y conversión
14. Crear `references/sequence_templates.md`
15. Implementar `sequence` y `convert`

---

## 9. Archivos Críticos de Referencia

| Archivo existente | Uso en el skill |
|-------------------|-----------------|
| `AiCodeDocumenter/Prompts/01_exclusion_list.md` | Fuente para `references/exclusion_list.md` |
| `AiCodeDocumenter/Prompts/00_identify_functional_groups.md` | Lógica base para `references/functional_groups_guide.md` |
| `AiCodeDocumenter/Prompts/02_generate_class_diagrams.md` | Estilos + reglas para `references/plantuml_styles.md` |
| `AiCodeDocumenter/Prompts/03_generate_component_diagram.md` | Templates para `references/c4_templates.md` |
| `AiCodeDocumenter/Prompts/04_generate_container_diagram.md` | Templates para `references/c4_templates.md` |
| `AiCodeDocumenter/Prompts/05_generate_sequence_diagrams.md` | Templates para `references/sequence_templates.md` |
| `AiCodeDocumenter/Tests/Test1/Output/License_functional_map.md` | Referencia de calidad para verificación |
| `AiCodeDocumenter/Tests/Test1/Output/Diagrams/Class/Checker.puml` | Referencia de calidad para verificación |
| `AiCodeReviewer/xml-xpp-parser/Invoke-AxSourceExtraction.ps1` | Script para comando `convert` |

---

## 10. Limitaciones Conocidas

- **El skill es instrucciones Markdown**, no código ejecutable. La "lógica" depende de que Claude interprete correctamente las instrucciones del SKILL.md
- **No compila PlantUML**: requiere Java + plantuml.jar (fuera de scope). Solo validación sintáctica básica
- **Consistencia entre invocaciones**: como LLM, los outputs pueden variar ligeramente entre ejecuciones
- **Contexto grande**: para proyectos con 200+ archivos .xpp, el Paso 1 (map) necesita leer todo el código. El skill debe advertir si supera ~5000 líneas y sugerir trabajar por lotes
- **Conversión XML→XPP** (comando `convert`): depende de PowerShell y de que los scripts existan en la ruta esperada
