
linux-headers:
  cmd.run:
    - name: apt-get install -y linux-headers-`uname -r` dkms

vboxguestadd-installed:
  vbox_guest.additions_installed

