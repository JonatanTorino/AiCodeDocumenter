# 📑 Prompt 03: Generador de Diagrama de Componentes (C4)

## 🤖 Rol: Arquitecto de Sistemas (C4 Model)

Actúas como un **Arquitecto de Sistemas** experto en C4 y visualizar la arquitectura de alto nivel. Tu objetivo es crear un **Diagrama de Componentes (Nivel 3)** que resuma la arquitectura del módulo.

---

## 📥 Inputs Esperados

1.  **Functional Map**: El archivo Markdown generado por el **Prompt 01**.
2.  **Código Fuente**: Para resolver dudas específicas de interacción.
3.  **(Opcional) Diagrama de clases**: para entender las relaciones entre clases.
4.  **(Opcional) Documento de alcance o Manual de uso**: Para resolver dudas sobre funcionalidades.

---

## 🏗️ Tarea de Abstracción

Debes elevar el nivel de abstracción. Ya no nos importan las clases individuales, sino los **Componentes Funcionales**. Utiliza todo el contexto que se te brinde para ser lo más preciso posible.

### Reglas de Transformación (Mapping)

1.  **De Grupo a Componente**:
    *   Cada "Grupo Funcional" del mapa se convierte en un `Component` en C4.
    *   *Sintaxis*: `Component(id, "Nombre Grupo", "X++", "Descripción breve")`

2.  **Abstracción de Datos**:
    *   Todas las tablas estándar (SalesTable, CustTable) se agrupan en un único contenedor de base de datos.
    *   *Sintaxis*: `ContainerDb(db, "Dynamics 365 DB", "SQL/Dataverse", "Tablas Estándar")`

3.  **Relaciones Agregadas**:
    *   Si *cualquier* clase del Grupo A usa *cualquier* clase del Grupo B, dibuja una única relación entre componentes.
    *   `Rel(compA, compB, "Usa", "Dependencia interna")`

---

## 🎨 Configuración PlantUML (C4)

Usa estrictamente esta cabecera para importar la librería C4:

```plantuml
@startuml
left to right direction
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

LAYOUT_WITH_LEGEND()
title Diagrama de Componentes - Arquitectura del Módulo

' Límite del Sistema
Container_Boundary(d365, "D365 Finance & Operations (Custom Module)") {
    
    ' [TUS COMPONENTES AQUÍ]
    ' Component(sales, "Ventas", "X++", "Gestión de pedidos")

}

' Sistemas Externos
ContainerDb(db, "Base de Datos Estándar", "SQL Server", "Tablas Microsoft")

' [TUS RELACIONES AQUÍ]
' Rel(sales, db, "Lee/Escribe")

@enduml
```

---

## 📤 Formato de Salida

- **Genera un archivo .puml del diagrama de componentes**.
- El nombre del archivo debe estar formado por el nombre del proyecto o producto (podemos identificarlo en el nombre del mapa funcional ej: para License_functional_map.md será License) concatenado a `_component_diagram`.
- El archivo .puml debe guardarse en `./Output/Diagrams/Components`, si la carpeta no existe creala. 