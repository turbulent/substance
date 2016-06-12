substance-salt-minion-config:
  file.blockreplace:
    - name: /etc/salt/minion
    - marker_start: "# BLOCK SALT/SUBSTANCE : minion"
    - marker_end: "# END BLOCK SALT/SUBSTANCE : minion"
    - content: |
        file_roots:
          base:
            - /srv/salt
            - /substance/devroot
    - show_changes: True
    - append_if_not_found: True

substance-salt-minion-restart:
  cmd.wait:
    - name: echo service salt-minion restart | at now + 1 minute
