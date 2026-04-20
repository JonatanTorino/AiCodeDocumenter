# 📘 Guía de Ejecución: Documentación Automatizada con IA (Dynamics 365 F&O)

Esta guía estandariza el flujo de trabajo para transformar código fuente X++ en documentación técnica y diagramas visuales utilizando prompts secuenciales.

---

## 📋 Pre-requisitos
1.  **Archivos de Código**: Acceso al repositorio de código fuente que se desea documentar. El código debe estar en formato .xpp. Si tiene los archivos en formato .xml conviertalos usando [Convertidor xml a xpp](../AiCodeReviewer/xml-xpp-parser/Invoke-AxSourceExtraction.ps1) siguiendo la guía [Guía convertidor xml a xpp](..\AiCodeReviewer\xml-xpp-parser\GEMINI.md).
2.  **Entorno de IA**: Acceso al LLM de su preferencia(debe soportar subida de archivos y ventanas de contexto amplias).
3.  **Repositorio de Prompts**: Tener los archivos `.md` de los prompts actualizados.

---

## 🔄 Resumen del Flujo de Trabajo

| Paso | Prompt a Ejecutar | Objetivo | Input Necesario | Input Opcional | Output Esperado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `00_identifiy_functional_groups.md` | **Descubrimiento** | Nombre del producto + Código | N/A | Archivo `[Nombre_del_producto]_[Fecha_hora].md` |
| **2** | `01_classify_classes.md` | **Mapeo Funcional** | Código + `[Nombre_del_producto]_[Fecha_hora].md` | N/A | Archivo `[Nombre_del_producto]_functional_map.md` |
| **3** | `02_generate_class_diagrams.md` | **Diagrama de Clases** | Código  + `[Nombre_del_producto]_functional_map.md` | N/A | Código PlantUML (Diagramas) |
| **4** | `03_generate_component_diagram.md` | **C4: Diagrama de Componentes** | Código  + `[Nombre_del_producto]_functional_map.md` | Doc de alcance y/o manual de uso | Diagrama C4 (Nivel 3) |
| **5** | `04_generate_container_diagram.md` | **C4: Diagrama de Contenedores** | Código  + `[Nombre_del_producto]_functional_map.md` | Doc de alcance y/o manual de uso | Diagrama C4 (Nivel 2) |
| **6** | `05_generate_sequence_diagrams.md` | **Diagramas de secuencia** | Documentación Funcional  + Código | `[Nombre_del_producto]_functional_map.md` | Diagramas de secuencia |
---

## 🚀 Ejecución Paso a Paso

### PASO 1: Identificación del Contexto de Negocio
**Objetivo:** Obtener una lista coherente de grupos funcionales para clasificar el código.

1.  Inicia una **nueva sesión** en la IA.
2.  Sube una muestra representativa de los archivos `.xpp`.
3.  Ejecuta el prompt **`00_identifiy_functional_groups.md`**.
    ```Ejemplo
        Sigue las instrucciones en @00_indentify_functional_groups.md aplicala en @Path_carpeta_con_codigo_xpp el producto se llama @Nombre_del_producto
    ```
4.  Responde las preguntas de la IA (si las hace).
5.  **Resultado:** La IA te dará un archivo  **`[Nombre_del_producto]_[Fecha_hora].md`** con los grupos generados el cuál se utilizará en los pasos posteriores.

---

### PASO 2: Clasificación y Mapa Funcional
**Objetivo:** Generar la tabla maestra que separa el código propio (Interno) de las referencias estándar (Externo).

1.  Asegúrate de tener subidos **todos** los archivos `.xpp` del modelo a documentar.
2.  Ejecuta el prompt **`01_classify_classes.md`**.
    ```Ejemplo
        Sigue las instrucciones en @01_classify_classes.md aplicalas usando @[Nombre_del_producto]_[Fecha_hora].md para los archivos en @Path_carpeta_con_codigo_xpp
    ```
3.  Proporciona el archivo de grupos obtenido en el Paso 1 como contexto.
4.  **Resultado:** La IA generará un archivo Markdown bajo el título **`[Nombre_del_producto]_functional_map.md`**.

---

### PASO 3: Generación de Diagramas de Clases (UML)
**Objetivo:** Crear diagramas de clases detallados con métodos, atributos y relaciones semánticas de cada grupo o del grupo funcional solicitado.

1.  **⚠️ IMPORTANTE:** Mantén la misma sesión del Paso 2 abierta (para que la IA recuerde el código). Si se cerró, debes volver a subir los `.xpp`.
2.  Ejecuta el prompt **`02_generate_class_diagrams.md`**.
    ```Ejemplo
        Sigue las instrucciones en @02_generate_class_diagrams.md apoyate en @[Nombre_del_producto]_functional_map.md y @Path_carpeta_con_codigo_xpp
    ```
3.  Proporciona tu archivo **`[Nombre_del_producto]_functional_map.md`** como contexto y la carpeta donde se encuentra el código fuente.
4.  **Resultado:** La IA generará los archivos con código **PlantUML** de los diagramas de clases para cada grupo funcional solicitado o por defecto para todos los grupos dentro de `[Nombre_del_producto]_functional_map.md`. Los nombres de estos diagramas estan compuestos por el nombre del grupo al que hacen referencia.

---

### PASO 4: Generación de Diagrama de Componentes (C4)
**Objetivo:** Crear diagramas de componentes, siguiendo la metodología C4, de cada grupo o del grupo funcional solicitado.

1.  **⚠️ IMPORTANTE:** Debes tener acceso al código fuente, el archivo `[Nombre_del_producto]_functional_map.md` y el prompt `03_generate_component_diagram.md` actualizado
2.  Ejecuta el prompt **`03_generate_component_diagram.md`**.
    ```Ejemplo
        Sigue las instrucciones en @03_generate_component_diagram.md apoyate en @[Nombre_del_producto]_functional_map.md y @Path_carpeta_con_codigo_xpp
    ```
3.  Proporciona tu archivo **`[Nombre_del_producto]_functional_map.md`** como contexto y la carpeta donde se encuentra el código fuente. Opcionalmente puedes agregar el manual de uso o el documento de alcance del proyecto.
4.  **Resultado:** La IA generará un archivo con código **PlantUML** del diagrama de componentes el nombre de este diagrama está compuesto por `[Nombre_del_producto]_component_diagram.md`.

---

### PASO 5: Generación de Diagrama de Contendedores (C4)
**Objetivo:** Crear diagramas de contenedores, siguiendo la metodología C4, de cada grupo o del grupo funcional solicitado.

1.  **⚠️ IMPORTANTE:** Debes tener acceso al código fuente, el archivo `[Nombre_del_producto]_functional_map.md` y el prompt `04_generate_container_diagram.md` actualizado
2.  Ejecuta el prompt **`04_generate_container_diagram.md`**.
    ```Ejemplo
        Sigue las instrucciones en @04_generate_container_diagram.md apoyate en @[Nombre_del_producto]_functional_map.md y @Path_carpeta_con_codigo_xpp
    ```
3.  Proporciona tu archivo **`[Nombre_del_producto]_functional_map.md`** como contexto y la carpeta donde se encuentra el código fuente. Opcionalmente puedes agregar el manual de uso o el documento de alcance del proyecto.
4.  **Resultado:** La IA generará un archivo con código **PlantUML** del diagrama de contenedores el nombre de este diagrama está compuesto por `[Nombre_del_producto]_container_diagram.md`

---

### PASO 6: Generación de Diagramas de Secuencia
**Objetivo:** Detallar el flujo dinámico (paso a paso) de los escenarios de negocio principales.

1. Copia el contenido del prompt **`05_generate_sequence_diagrams.md`**.
    ```Ejemplo
        Sigue las instrucciones en @05_generate_sequence_diagrams.md. Analiza los casos de usos descritos en @Manual_de_Usuario.md y traza la ejecución en @Path_carpeta_con_codigo_xpp
    ```
2. **Inputs críticos**:
    - **Documentación Funcional**: Sube el Manual de Uso, Documento de Alcance o describe el escenario textualmente (ej: "Proceso de confirmación de factura").
    - **Código Fuente**: Asegurate de adjuntar los archivos .xpp correspondientes.
3. **Resultado:**: La IA generará múltiples diagramas de secuencia (archivos .puml) guardados en ./Output/Diagrams/Sequence/, diferenciando visualmente entre UI (Forms), Lógica y Datos.

---

## ❓ Solución de Problemas Frecuentes

### "La IA dice que no hay grupos definidos en el Paso 2"
* **Causa:** No proporcionaste la lista de grupos en el prompt `01_classify_classes.md` antes de enviarlo.
* **Solución:** Nombra manualmente los grupos predefinidos que deseas que se utilicen en el prompt `01_classify_classes.md`.

### "El diagrama de clases tiene cajas vacías (sin métodos)"
* **Causa:** La IA "olvidó" el contenido de los archivos o iniciaste una sesión nueva solo con el mapa.
* **Solución:** Antes de ejecutar el Paso 3, sube nuevamente los archivos `.xpp` y dile a la IA: *"Aquí tienes el código fuente para que analices sus métodos"*.

### "El diagrama es demasiado grande para leerse"
* **Solución:** No pidas todos los grupos a la vez. Pide a la IA: *"Genera el diagrama PlantUML solo para el grupo [Nombre del Grupo]"*.