# 🚫 Diccionario de Exclusión de Clases

Este listado contiene las clases, tipos de datos y componentes del sistema que deben ser **IGNORADOS** al generar diagramas de dependencia funcional, ya que representan "ruido" técnico y no lógica de negocio.

## 1. Tipos de Datos Primitivos y Colecciones
* str, int, int64, real, boolean, date, time, utcdatetime, void, anytype
* container, guid
* List, ListEnumerator, Set, SetEnumerator, Map, MapEnumerator
* Array, Struct

## 2. Framework UI & Formularios
* Args
* FormRun, FormObjectSet, FormDataSource
* FormControl, FormBuildControl, FormStringControl, FormIntControl, FormRealControl, FormDateControl, FormCheckBoxControl, FormButtonControl, FormComboBoxControl, FormGroupControl, FormTabControl, FormTabPageControl, FormGridControl
* Dialog, DialogField, DialogGroup
* Box

## 3. Clases Base del Sistema (Kernel/Platform)
* Object, Global, Application, ClassFactory
* xSession, xApplication, xGlobal, xInfo
* Session, UserInfo
* RunBase, RunBaseBatch (Ignorar la base, pero NO las clases que heredan si son de negocio)
* SysOperation* (Framework clases, ej: SysOperationServiceController)

## 4. Base de Datos y Consultas
* Query, QueryRun, QueryBuildDataSource, QueryBuildRange
* RecordInsertList
* Connection, UserConnection, Statement, ResultSet
* Common (La clase base de las tablas)

## 5. Excepciones y Logging
* Exception
* Error, Warning, Info
* SysInfolog