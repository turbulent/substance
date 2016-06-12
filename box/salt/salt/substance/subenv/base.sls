{% from 'substance/init.sls' import subst with context %}
{% from 'substance/subenv/settings.sls' import subenv with context %}

{{subenv.root}}:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subenv.root}}/pids:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subenv.root}}/code:
  file.symlink:
    - target: {{subenv.codeRoot}}

{{subenv.root}}/database:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subenv.root}}/data:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775


{{subenv.root}}/logs:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subenv.root}}/spool:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subenv.root}}/conf:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 755

{%- if salt['file.file_exists'](subenv.codeRoot + "/subenv/" + 'containers.jinja') %}
{{subenv.root}}/containers.yml:
  file.managed:
    - template: jinja
    - source: file://{{subenv.codeRoot}}/subenv/containers.jinja
    - user: {{subst.user}}
    - group: {{subst.group}}
    - mode: 644
    - context:
      subst: {{subst}}
      subenv: {{subenv}}
{%- endif %}

