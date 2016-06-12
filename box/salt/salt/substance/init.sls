{% set p = salt['pillar.get'] %}

{% set user = p('substance:user') %}
{% set group = p('substance:group') %}
{% set envsRoot = p('substance:roots:envs') %}
{% set devRoot = p('substance:roots:dev') %}
{% set currentRoot = p('substance:roots:current') %}

{% set subst = {} %}

{% do subst.update({
  'pillar': p,
  'user': user,
  'group': group,
  'envsRoot': envsRoot,
  'devRoot': devRoot,
  'currentRoot': currentRoot
}) %} 

