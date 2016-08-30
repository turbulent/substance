
substance-network-interfaces:
  file.managed:
    - name: /etc/network/interfaces
    - contents: |
        auto lo
        iface lo inet loopback
        auto eth0
        iface eth0 inet dhcp
        auto eth1
        iface eth1 inet dhcp

substance-sshd-config:
  file.blockreplace:
    - name: /etc/ssh/sshd_config
    - marker_start: "# BLOCK SALT/SUBSTANCE : ssh"
    - marker_end: "# END BLOCK SALT/SUBSTANCE : ssh"
    - content: |
        PermitOpen any
        AllowTcpForwarding yes
        StrictModes no
    - show_changes: True
    - append_if_not_found: True


substance-sshd-restart:
  cmd.run:
    - name: service ssh restart
