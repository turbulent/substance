{% from 'substance/init.sls' import subst with context %}

{% set root = subst.envsRoot + "/" + subst.pillar('subenv:project') %}
{% set codeRoot = subst.devRoot + "/" + subst.pillar('subenv:project') %}
{% set project = subst.pillar('subenv:project') %}
{% set fqdn = subst.pillar('subenv:fqdn') %}

{% set subenv = {} %}
{% do subenv.update({
  'pillar': subst.pillar,
  'project': project,
  'fqdn': fqdn,
  'root': root,
  'codeRoot': codeRoot
}) %}
