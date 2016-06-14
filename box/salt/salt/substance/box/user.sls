
root-user-passwd:
  user.present:
    - name: root
    - password: $1$TrXYiiww$ND61zlw7wRth3..tzmlYO.
    - enforce_password: true
    - uid: 0

substance-user:
  user:
    - name: substance
    - present
    - uid: 1000
    - password: $1$TrXYiiww$ND61zlw7wRth3..tzmlYO.
    - enforce_password: true
    - home: /substance
    - shell: /bin/bash


substance-user-dotssh:
  file.directory:
    - name: /substance/.ssh
    - user: substance
    - group: substance
    - mode: 700

AAAAB3NzaC1yc2EAAAADAQABAAABAQC9KutC+/Zwowb/Tnw+xbjGCKmTlSzTcM4i1BI3MCIZuA5pajVNz4/Uxmx3DkATGdsi82WhGg0HknG5AS+9s6P6z9dhlPCjghbL8LlM253KqVGjEEI0cE8GkpvJS8IY8iqYICCE1ib73qxx/3ASL06r5Z0TIeg7draClTNrIf6xn85Ty/GJ1SMrmJ72N/R3+6YDIN9LLGi2Ze/05mQb6kn8Ue4Iu/kAcjqCBZYZKfKaiMsGH9AL2YDziccTtAn0vnTbK8FeXsadX+QybhagYLopjs7x8zGCZB8qGMCD40OX6vTTPq+X5hjrvAgjogR4uZDIZvyNZTMMFm/B1V3LEKLP:
  ssh_auth.present:
    - user: substance
    - enc: ssh-rsa
    - comment: "substance_insecure"

/etc/sudoers.d/substance:
  file.managed:
    - contents: "substance ALL=(ALL) NOPASSWD:ALL"

/etc/sudoers:
  file.append:
    - text: 
      - "Defaults env_keep += SSH_AUTH_SOCK"
