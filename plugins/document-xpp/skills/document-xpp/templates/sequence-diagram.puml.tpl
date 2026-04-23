@startuml {{slug}}-{{flow_slug}}

!theme plain
autonumber
skinparam responseMessageBelowArrow true

skinparam participant {
    BackgroundColor<<Form>>     #F3E5F5
    BorderColor<<Form>>         #7B1FA2
    BackgroundColor<<Table>>    #E8F5E9
    BorderColor<<Table>>        #2E7D32
    BackgroundColor<<External>> #ECEFF1
    BorderColor<<External>>     #B0BEC5
}

title {{flow_name}}

actor "Usuario" as User

box "Presentation" #FAFAFA
{{#presentation_participants}}
    participant "{{label}}" as {{alias}} <<Form>>
{{/presentation_participants}}
end box

box "Business Logic" #FAFAFA
{{#business_participants}}
    participant "{{label}}" as {{alias}}
{{/business_participants}}
end box

box "Data" #FAFAFA
{{#data_participants}}
    participant "{{label}}" as {{alias}} <<Table>>
{{/data_participants}}
end box

{{#external_participants}}
participant "{{label}}" as {{alias}} <<External>>
{{/external_participants}}

' --- Flujo ---
{{flow_steps}}

@enduml
