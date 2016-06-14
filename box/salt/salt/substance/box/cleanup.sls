provisioner-cleanup-script:
  file.managed:
    - name: /substance/provisioner-cleanup.sh
    - user: root
    - group: root
    - contents: |
        #!/bin/bash
        rm -f /etc/init/provisioner-cleanup.conf
        rm -f /etc/sudoers.d/packer 
        userdel -rf packer
        rm -- "$0"

provisioner-cleanup-unit:
  file.managed:
    - name: /etc/init/provisioner-cleanup.conf
    - user: root
    - group: root
    - mode: 755
    - contents: |
        # Remove the packer user next shutdown.
        start on runlevel [016] or deconfiguring-networking
        task
        exec /substance/provisioner-cleanup.sh
