pkg.upgrade:
    module.run

apt-transport-https:
  pkg:
    - installed

ca-certificates:
  pkg:
    - installed

acpid:
  pkg: 
    - installed

python-pip:
  pkg:
    - installed

python-dev:
  pkg:
    - installed

libffi-dev:
  pkg:
    - installed

libssl-dev:
  pkg:
    - installed

rsync:
  pkg:
    - installed

setuptools:
  cmd.run:
    - name: pip install --upgrade setuptools 

