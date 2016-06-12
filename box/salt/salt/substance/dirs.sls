{% from 'substance/init.sls' import subst with context %}

{{subst.envsRoot}}:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775

{{subst.devRoot}}:
  file.directory:
    - makedirs: True
    - user: {{subst.user}}
    - group: {{subst.group}}
    - dirmode: 775
