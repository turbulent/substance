

substance-dockwrkr:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/turbulent/dockwrkr.git

substance-subwatch:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git

substance-substance:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git

substance-subwatch-init:
  file.managed:
    - name: /etc/init/subwatch.conf
    - source: salt://substance/box/subwatch.conf
    - mode: 644
