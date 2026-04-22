@startuml {{slug}}-detailed
!include <C4/C4_Component.puml>

title {{group_name}} — Sub-componentes (Nivel 2 Detallado)

' --------------------------------------------------------------------
' Boundary del grupo funcional. El agente `c4-component-writer`
' rellena {{#clusters}} agrupando nodes[] por role/artifact_kind:
'   service/controller → "Servicios" / "Controladores"
'   dto                → "Contratos"
'   table              → "Tablas"
'   view               → "Vistas"
'   helper/other       → "Utilidades"
' Clusters con 0 clases se omiten.
' NO se exponen clases individuales — el nivel de abstracción
' son los clusters semánticos, no las clases.
' --------------------------------------------------------------------
Container_Boundary(group, "{{group_name}}") {

{{#clusters}}
  Component({{alias}}, "{{label}}", "X++", "{{description}}")
{{/clusters}}

}

' --------------------------------------------------------------------
' Componentes externos relacionados — otros grupos del módulo que
' este grupo referencia (external_refs[].in_inventory=true).
' Se renderizan fuera del boundary con Component_Ext.
' --------------------------------------------------------------------
{{#external_components}}
Component_Ext({{alias}}, "{{label}}", "X++", "")
{{/external_components}}

' --------------------------------------------------------------------
' Relaciones entre clusters y externos.
' --------------------------------------------------------------------
{{#relations}}
Rel({{from}}, {{to}}, "{{label}}")
{{/relations}}

SHOW_LEGEND()

@enduml
