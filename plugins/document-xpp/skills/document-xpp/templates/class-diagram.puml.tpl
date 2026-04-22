@startuml {{slug}}

title {{group_name}}

' --------------------------------------------------------------------
' Paleta global — aplicar por stereotype, NUNCA per-clase con !define.
' Mantener siempre la paleta completa aunque no uses todos los roles;
' deja el archivo uniforme entre diagramas del mismo workspace.
' Fuente: references/visual-conventions.md
' --------------------------------------------------------------------
skinparam class {
  BackgroundColor<<Service>>     #A5D6A7
  BackgroundColor<<Controller>>  #FFCC80
  BackgroundColor<<Table>>       #81D4FA
  BackgroundColor<<View>>        #81D4FA
  BackgroundColor<<Entity>>      #81D4FA
  BackgroundColor<<Contract>>    #FFF59D
  BackgroundColor<<DTO>>         #FFF59D
  BackgroundColor<<Helper>>      #CFD8DC
  BackgroundColor<<EDT>>         #FCE4EC
  BackgroundColor<<External>>    #ECEFF1
  BorderColor<<External>>        #B0BEC5
  BorderStyle<<External>>        dashed
}
skinparam enum {
  BackgroundColor #F8BBD0
}

' Layout default — top-to-bottom. Cambiar a `left to right direction`
' si el flujo del grupo es claramente horizontal (Controller -> Service
' -> HttpService -> External) y el diagrama queda más legible.
top to bottom direction

' --------------------------------------------------------------------
' Clases del grupo
' --------------------------------------------------------------------
{{#nodes}}
class {{class}} <<{{stereotype}}>> {
{{#members}}
  {{.}}
{{/members}}
}
{{/nodes}}

' --------------------------------------------------------------------
' Clases externas referenciadas (si las hay)
' --------------------------------------------------------------------
{{#externals}}
class {{class}} <<{{stereotype}}>>
{{/externals}}

' --------------------------------------------------------------------
' Relaciones — primero herencias/implementaciones, después asociaciones,
' después composiciones/agregaciones. Verbo del catálogo (o registrado
' como warning si es nuevo).
' --------------------------------------------------------------------
{{#inheritances}}
{{from}} --|> {{to}}
{{/inheritances}}

{{#implementations}}
{{from}} ..|> {{to}}
{{/implementations}}

{{#associations}}
{{from}} {{arrow}} {{to}} : {{verb}}
{{/associations}}

{{#compositions}}
{{from}} *-- {{to}} : contiene
{{/compositions}}

{{#aggregations}}
{{from}} o-- {{to}} : pertenece a
{{/aggregations}}

' --------------------------------------------------------------------
' Notas — máximo 2. Usar sólo para:
'   - marcar el entry point del flujo
'   - señalar una asimetría no obvia
'   - flagear un gotcha
' NO usar para repetir lo que el stereotype + color ya comunican.
' --------------------------------------------------------------------
{{#notes}}
note {{position}} of {{target}}
  {{text}}
end note
{{/notes}}

' --------------------------------------------------------------------
' Leyenda — sólo los roles efectivamente presentes en el diagrama.
' --------------------------------------------------------------------
legend right
  |= Color |= Rol |
{{#legend_rows}}
  |<back:{{color}}>            </back>| {{role}} |
{{/legend_rows}}
end legend

@enduml
