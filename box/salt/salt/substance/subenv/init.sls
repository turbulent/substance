{% from 'substance/subenv/settings.sls' import subenv with context %}

include:
  - .base
{%- if salt['file.file_exists'](subenv.codeRoot + "/subenv/" + 'init.sls') %}
  - {{subenv.project}}.subenv
{%- endif %}
