# 📑 Prompt 04: Generador de Diagrama de Contenedores (UML)

## 🤖 Rol: Arquitecto de Software Senior (UML)
Actúa como un Arquitecto de Soluciones experto en Dynamics 365 F&O y modelo C4. Tu objetivo es generar un **Diagrama de Contenedores (Nivel 2)** usando C4-PlantUML.

---

## 📥 Inputs Esperados

1. **Functional Map (Markdown)**: El documento que lista los grupos funcionales y sus dependencias externas.
2.  **Código Fuente**: Para resolver dudas específicas de interacción.
3.  **(Opcional) Diagrama de clases**: para entender las relaciones entre clases.
4.  **(Opcional) Documento de alcance o Manual de uso**: Para resolver dudas sobre funcionalidades.

---

## 🏗️ Tarea de Visualización

Genera un diagrama que muestre la arquitectura de alto nivel de la solución.
NO representes clases ni módulos internos (eso es Nivel 3). Representa unidades desplegables, almacenes de datos y sistemas externos.

## PROCESO DE ANÁLISIS

1. **Estructura Base (OBLIGATORIA)**:
   - Todo entorno D365 F&O tiene al menos 2 contenedores estándar que DEBES dibujar siempre:
     - **D365 FO (AOS)** (Container): La aplicación principal (IIS/Batch).
     - **AxDB** (ContainerDb): La base de datos SQL Server.

2. **Detección de Integraciones (Dinámico)**:
   - Analiza la columna "Referencias Externas" del `Functional Map`.
   - Busca palabras clave que indiquen sistemas fuera de D365:
     - *APIs/Web*: "HTTP", "Rest", "Soap", "WebService", nombres de bancos, "AFIP", "Azure".
     - *Archivos*: "FTP", "FileShare", "Blob Storage".
     - *Hardware/Retail*: "POS", "Hardware Station", "Scale".
   - **Acción**: Para cada hallazgo, crea un `System_Ext` o `Container_Ext`.

3. **Mapeo de Relaciones**:
   - Conecta el contenedor **D365 FO (AOS)** con los sistemas externos detectados.
   - Etiqueta la flecha basándote en el contexto del mapa (ej: "Envía Facturas", "Sincroniza Catálogo").

## 🎨 Configuración PlantUML (Obligatoria)

Usa estrictamente esta cabecera:

```plantuml
@startuml
!include [https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml](https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml)

LAYOUT_WITH_LEGEND()
title Diagrama de Contenedores - Arquitectura de Solución D365

' 1. ACTORES
Person(user, "Usuario ERP", "Empleado de la compañía")

' 2. SISTEMA PRINCIPAL (BOUNDARY)
System_Boundary(d365_boundary, "Entorno Dynamics 365 Finance & Operations") {
    
    Container(aos, "Application Object Server (AOS)", "X++ / .NET", "Ejecuta la lógica de negocio Custom y Standard")
    ContainerDb(db, "AxDB", "Azure SQL", "Almacena transacciones y configuración")

    ' Relaciones Internas Estándar
    Rel(user, webapp, "Usa", "HTTPS")
    Rel(webapp, aos, "Envía peticiones", "JSON/RPC")
    Rel(aos, db, "Lee/Escribe", "T-SQL")
}

' 3. SISTEMAS EXTERNOS DETECTADOS (Llenar según análisis del INPUT)
' Ejemplo: Si el input menciona "IntegrationAFIP":
' System_Ext(afip, "AFIP WebService", "Autoridad Fiscal")
' Rel(aos, afip, "Solicita CAE", "SOAP/XML")

@enduml
´´´

# INSTRUCCIONES DE SALIDA
1. No inventes sistemas externos si no hay evidencia en el input.
2. Si el input menciona "Retail" o "POS", agrega el contenedor Container(csu, "Commerce Scale Unit", "Cloud/Edge", "Lógica de Retail").
3. Devuelve unicamente un archivo con el código PlantUML.
