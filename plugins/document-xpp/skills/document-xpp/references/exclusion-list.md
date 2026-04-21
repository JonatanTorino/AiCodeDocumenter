# Lista de exclusión — ruido técnico de D365 F&O / X++

Clases, tipos de datos y componentes del framework que el `functional-classifier` **debe ignorar** al calcular referencias externas y al proponer grupos funcionales. Su presencia en `dependencies.csv` no agrega información de negocio — sólo infla el grafo.

**Regla de aplicación:** si el `to_class` de una fila de `dependencies.csv` coincide exactamente (case-insensitive) con alguno de los nombres listados acá, se descarta.

---

## 1. Tipos primitivos y colecciones built-in

- `str`, `int`, `int64`, `real`, `boolean`, `date`, `time`, `utcdatetime`, `timeofday`, `void`, `anytype`
- `container`, `guid`
- `List`, `ListEnumerator`, `ListIterator`
- `Set`, `SetEnumerator`, `SetIterator`
- `Map`, `MapEnumerator`, `MapIterator`
- `Array`
- `Struct`

---

## 2. Framework de formularios y UI

- `Args`
- `FormRun`, `FormDataSource`, `FormObjectSet`
- `FormControl`, `FormBuildControl`
- `FormStringControl`, `FormIntControl`, `FormRealControl`, `FormDateControl`, `FormCheckBoxControl`, `FormButtonControl`, `FormComboBoxControl`, `FormGroupControl`, `FormTabControl`, `FormTabPageControl`, `FormGridControl`, `FormTreeControl`, `FormActionPaneControl`
- `Dialog`, `DialogField`, `DialogGroup`, `DialogRunbase`
- `Box`, `Info`, `Warning`, `Error`

---

## 3. Clases base del kernel y plataforma

- `Object`, `Global`, `Application`, `ClassFactory`
- `xSession`, `xApplication`, `xGlobal`, `xInfo`, `xRecord`
- `Session`, `UserInfo`
- `RunBase`, `RunBaseBatch`, `RunBaseSerializable` — *la base se excluye; las clases de negocio que heredan de ellas NO se excluyen*
- `SysOperationServiceController`, `SysOperationController`, `SysOperationContract`, `SysOperationDataContract` — *las bases del framework SysOperation se excluyen; los contratos específicos del dominio NO*
- `SysOperationProcess`

---

## 4. Acceso a datos y consultas

- `Query`, `QueryRun`, `QueryBuildDataSource`, `QueryBuildRange`, `QueryBuildLink`, `QueryFilter`
- `RecordInsertList`, `RecordSortedList`
- `Connection`, `UserConnection`, `Statement`, `ResultSet`, `SqlDataDictionary`
- `Common` — *la base de todas las tablas; las tablas específicas del dominio NO se excluyen*
- `CompanyInfo`, `DataArea`, `DataAreaId` — scope multicompañía

---

## 5. Excepciones, logging e infolog

- `Exception`
- `SysInfolog`, `SysInfologMessageStruct`
- `Error`, `Warning`, `Info`, `Debug` (las funciones globales homónimas — si aparecen como clase, ignorar)
- `EventLog`, `xEventLog`

---

## 6. Utilidades de cadenas, números y fechas

- `strFmt`, `strLRTrim`, `strRem`, `subStr` (funciones globales, raramente aparecen como dependencia de clase — incluir por las dudas)
- `num2Str`, `str2Num`, `str2Int`, `str2Date`
- `DateTimeUtil`

---

## 7. Seguridad y roles

- `SecurityRole`, `SecurityPrivilege`, `SecurityDuty`
- `SecurityRightsOfUser`, `SysSecUserManager`

---

## 8. Reflexión y metadata

- `DictClass`, `DictTable`, `DictMethod`, `DictField`, `DictEnum`, `DictView`
- `SysDictClass`, `SysDictTable`, `SysDictMethod`, `SysDictField`, `SysDictEnum`
- `TreeNode`, `xTreeNode`

---

## 9. Serialización e interop

- `XmlDocument`, `XmlElement`, `XmlNode`, `XmlNodeList`, `XmlAttribute`, `XmlReader`, `XmlWriter`, `XmlTextReader`, `XmlTextWriter`
- `JsonReader`, `JsonWriter`
- `System.Object`, `System.String`, `System.Int32`, `System.Int64`, `System.Exception`, `System.DateTime`, `System.TimeSpan` (interop con .NET base types)

---

## 10. Batch y eventos

- `BatchHeader`, `BatchRun`, `BatchInfo`
- `SysDaEventContext`, `SysDaEventBinding`

---

## Convención de mantenimiento

- Si al validar un mapa funcional aparecen referencias externas que evidentemente son ruido técnico pero no están acá, **agregarlas** con un commit y un comentario breve. No son inmutables.
- Si una clase legítima del dominio coincide por accidente con un nombre de esta lista, el `functional-classifier` debe preferir la presencia en `inventory.csv` — lo que está en el inventario NUNCA es ruido.
