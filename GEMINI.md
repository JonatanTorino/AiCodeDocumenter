# Contexto AiCodeDocumenter

Este directorio contiene el flujo de trabajo y los activos para la **Documentación Técnica Automatizada** de soluciones Dynamics 365 F&O utilizando IA.

## Guía de Uso
- **`GuiaParaDocTecnica.md`**: Documento maestro que explica paso a paso cómo ejecutar el flujo de documentación.

## Estructura de Directorios
- **`Prompts/`**: Conjunto secuencial de prompts para guiar a la IA:
    - `00_identify_functional_groups`: Identificación de grupos funcionales.
    - `01_classify_classes`: Mapeo de clases a grupos e identificación de dependencias.
    - `01_exclusion_list`: Diccionario de clases y componentes del sistema a ignorar (ruido técnico).
    - `02_generate_class_diagrams`: Generación de diagramas de clases PlantUML.
    - `03_generate_component_diagram`: Generación de diagramas de componentes C4 (Nivel 3).
    - `04_generate_container_diagram`: Generación de diagramas de contenedores C4 (Nivel 2).
    - `05_generate_sequence_diagrams`: Generación de diagramas de secuencia para modelado de comportamiento.
- **`Output/`**: Directorio de destino para los entregables finales.
    - **`Diagrams/`**: Representaciones visuales generadas (Clases, Componentes, Contenedores, Secuencia).
- **`.Drafts/`**: Almacenamiento temporal de documentación en proceso.
    - **`DocsByFile/`**: Documentación técnica individual generada por cada artefacto analizado.
- **`Tests/`**: Casos de prueba y resultados de validación del flujo de documentación.

## Propósito
Estandarizar la generación de documentación técnica de alta calidad mediante:
1.  El análisis del código fuente X++ para identificar patrones arquitectónicos.
2.  La generación de diagramas visuales (UML, C4).
3.  La producción de documentación detallada en markdown para componentes específicos del sistema.

## Protocolos

### Sincronización de Prompts
Mantener siempre actualizada la sección **Estructura de Directorios** de este archivo (`GEMINI.md`) para que refleje fielmente los archivos existentes en la carpeta `Prompts/` y sus propósitos actuales.
