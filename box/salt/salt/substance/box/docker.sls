substance-docker-repo:
  pkgrepo.managed:
    - humanname: Docker Ubuntu packages
    - name: deb https://apt.dockerproject.org/repo ubuntu-trusty main
    - file: /etc/apt/sources.list.d/docker.list
    - keyid: 58118E89F3A912897C070ADBF76221572C52609D
    - keyserver: p80.pool.sks-keyservers.net
    - require_in:
      - state: substance-docker-engine

substance-docker-engine:
  pkg.installed:
    - name: docker-engine
    - version: 1.10.3-0~trusty

substance-aufs:
  pkg.installed:
    - pkgs:
      - linux-image-extra-{{ grains.get('kernelrelease') }}
      - aufs-tools

substance-docker-defaults:
  file.blockreplace:
    - name: /etc/default/docker
    - marker_start: "# BLOCK SALT/SUBSTANCE : docker options"
    - marker_end: "# /BLOCK SALT/SUBSTANCE : docker options"
    - content: |
        DOCKER_OPTS="--userland-proxy=false --storage-driver=aufs -H 0.0.0.0:2375"

    - show_changes: True
    - append_if_not_found: True

substance-docker-env:
  file.blockreplace:
    - name: /etc/environment
    - marker_start: "# BLOCK SALT/SUBSTANCE : docker options"
    - marker_end: "# /BLOCK SALT/SUBSTANCE : docker options"
    - content: DOCKER_HOST="tcp://127.0.0.1:2375"
    - show_changes: True
    - append_if_not_found: True

substance-docker-restart:
  cmd.run: 
    - name: service docker restart

substance-user-group-docker:
  group.present:
    - name: docker
    - members:
      - substance  
