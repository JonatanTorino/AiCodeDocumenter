# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito del Repositorio

Este directorio contiene un **flujo de trabajo de Documentación Técnica Automatizada** para soluciones Dynamics 365 F&O. No es un proyecto de software tradicional: es un sistema de prompts secuenciales que se ejecutan en un LLM externo (Gemini, Grok, Claude, etc.) para transformar código fuente X++ en documentación técnica y diagramas visuales.

No hay código ejecutable, tests ni build en este directorio. El trabajo principal consiste en mantener y mejorar los prompts en `Prompts/`.

## Flujo de Trabajo Principal

El proceso se ejecuta en 6 pasos secuenciales, cada uno con su prompt correspondiente en `Prompts/`:

| Paso | Archivo de Prompt | Output |
|------|------------------|--------|
| 1 | `00_identify_functional_groups.md` | `Output/[Producto]_[fecha].md` |
| 2 | `01_classify_classes.md` | `Output/[Producto]_functional_map.md` |
| 3 | `02_generate_class_diagrams.md` | `Output/Diagrams/Class/*.puml` |
| 4 | `03_generate_component_diagram.md` | `Output/Diagrams/Components/*.puml` |
| 5 | `04_generate_container_diagram.md` | `Output/Diagrams/Containers/*.puml` |
| 6 | `05_generate_sequence_diagrams.md` | `Output/Diagrams/Sequence/*.puml` |

El archivo `01_exclusion_list.md` es un diccionario de clases estándar de D365/X++ que los prompts deben ignorar (ruido técnico). Se usa como contexto en el Paso 2.

## Convenciones de los Prompts

### Inputs del código fuente
- El código fuente X++ está en archivos `.xpp` (pueden generarse desde `.xml` con `../AiCodeReviewer/xml-xpp-parser/Invoke-AxSourceExtraction.ps1`).
- Los artefactos X++ siguen la nomenclatura: `[Prefijo][Infijo_Funcional][Nombre].xpp` (ej: `AxnLicSubscriptionService.xpp`).
- Los prefijos de proyecto suelen ser 3 caracteres (ej: `Axn`, `Axx`, `Cus`).

### Outputs esperados
- Todos los outputs se guardan en `Output/`.
- Los diagramas son PlantUML (`.puml`) con estilos visuales estandarizados:
  - Clases internas: fondo gris claro
  - Tablas internas (`<<Table>>`): fondo verde
  - Referencias externas (`<<External>>`): fondo azul
- Los diagramas de secuencia usan 3 capas (Presentation, Business Logic, Data Layer).

### Functional Map
El archivo `[Producto]_functional_map.md` es el artefacto pivote del flujo: lo produce el Paso 2 y lo consumen los Pasos 3, 4, 5 y 6. Su formato es una tabla Markdown con columnas `Clase | Referencias Internas | Referencias Externas` agrupadas por grupo funcional.

## Estructura de Directorios Relevante

- `Prompts/` — Prompts secuenciales (el activo principal a mantener)
- `Output/` — Entregables generados por el flujo (documentación y diagramas)
- `.Drafts/` — Documentación en proceso / borradores de trabajo
- `Tests/` — Casos de prueba con outputs de distintos LLMs (Test1=Claude, Test2=Grok/KiloCode, Test3=Gemini)
- `GuiaParaDocTecnica.md` — Documento maestro de ejecución paso a paso

## Protocolo de Mantenimiento

Cuando se agreguen, renombren o eliminen archivos en `Prompts/`, actualizar la sección **Estructura de Directorios** de `GEMINI.md` para mantenerla sincronizada. Este protocolo está definido en `GEMINI.md`.
