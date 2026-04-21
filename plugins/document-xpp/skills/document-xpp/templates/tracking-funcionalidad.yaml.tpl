# Template: _tracking/funcionalidades/<slug>.yaml
# Placeholders entre {{ }} a reemplazar por el workflow 02.
# Schema completo documentado en references/tracking-schema.md
name: {{NAME}}
slug: {{SLUG}}
description: >
  {{DESCRIPTION}}
created_at: {{CREATED_AT_ISO8601}}
last_updated: {{LAST_UPDATED_ISO8601}}
status: {{STATUS}}

classes: {{CLASSES_YAML_LIST}}
# Formato esperado de cada item:
#   - file: <path relativo al XppSource>
#     class: <NombreClase>
#     role: <service|entity|controller|dto|helper|other>

inputs_registered:
  scope: {{SCOPE_PATHS_YAML_LIST}}
  manuals: {{MANUAL_PATHS_YAML_LIST}}
  previous_diagrams: {{PREVIOUS_DIAGRAMS_YAML_LIST}}

artifacts:
  class_diagram: ""
  sequence_diagrams: []
  component_diagrams:
    level_1_node_in: ""
    level_2: ""
