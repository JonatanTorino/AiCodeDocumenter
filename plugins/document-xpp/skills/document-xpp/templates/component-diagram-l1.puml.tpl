@startuml {{slug}}-conceptual
!include <C4/C4_Component.puml>

title {{module_name}} — Componentes (Nivel 1 Conceptual)

' --------------------------------------------------------------------
' Boundary del módulo — contiene un componente por grupo funcional.
' El agente `c4-component-writer` rellena los bloques {{#components}}
' leyendo todos los funcionalidades/*.yaml del workspace.
' --------------------------------------------------------------------
Container_Boundary(module, "{{module_name}}") {

{{#components}}
  Component({{alias}}, "{{label}}", "X++", "{{description}}")
{{/components}}

}

' --------------------------------------------------------------------
' Componentes externos referenciados (external_refs[].in_inventory=true
' de algún diagram_candidates/*.yaml). Sólo se renderiza si hay al
' menos una relación entrante/saliente que los involucre.
' --------------------------------------------------------------------
{{#external_components}}
Component_Ext({{alias}}, "{{label}}", "X++", "{{description}}")
{{/external_components}}

' --------------------------------------------------------------------
' Relaciones — derivadas de external_refs[].{in_inventory: true,
' other_group_slug} en los diagram_candidates/*.yaml.
' El label usa el vocabulario de visual-conventions.md.
' --------------------------------------------------------------------
{{#relations}}
Rel({{from}}, {{to}}, "{{label}}")
{{/relations}}

SHOW_LEGEND()

@enduml
