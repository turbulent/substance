

substance-dockwrkr:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/turbulent/dockwrkr.git@1.0

substance-subwatch:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@1.0

substance-substance:
  cmd.run:
    - name: pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@0.6a2

substance-subwatch-init:
  file.managed:
    - name: /etc/init/subwatch.conf
    - source: salt://substance/box/subwatch.conf
    - mode: 644
