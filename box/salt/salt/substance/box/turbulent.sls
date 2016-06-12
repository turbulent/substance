turbulent-hosts-docker-registry:
  file.blockreplace:
    - name: /etc/hosts
    - marker_start: "# BLOCK SALT/SUBSTANCE : turbulent hosts"
    - marker_end: "# END BLOCK SALT/SUBSTANCE : turbulent hosts"
    - content: |
        10.0.20.35 docker-registry 
    - show_changes: True
    - append_if_not_found: True

turbulent-substance-dotssh-known-github.com:
  ssh_known_hosts:
    - present
    - name: github.com
    - user: substance
    - fingerprint: 16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48

turbulent-substance-dotssh-known-gitlab:
  ssh_known_hosts:
    - present
    - name: gitlab.turbulent.ca
    - port: 6666
    - user: substance

turbulent-gitlab-ssh-config:
  file.blockreplace:
    - name: /substance/.ssh/config
    - marker_start: "# BLOCK SALT/SUBSTANCE : turbulent hosts"
    - marker_end: "# END BLOCK SALT/SUBSTANCE : turbulent hosts"
    - content: |
      Host: gitlab.turbulent.ca
        User git
        Port 6666
        StrictHostKeyChecking no
    - show_changes: True
    - append_if_not_found: True

turbulent-substance-ssh-config:
  file.exists:
    - name: /substance/.ssh/config
    - user: substance
    - group: substance
    - mode: 700 

turbulent-git-config-push:
  cmd.run:
    - name: git config --global push.default simple
    - user: substance
    - cwd: /substance
