from setuptools import setup, find_packages
import platform

with open('README.rst') as f:
    readme = f.read()

execfile('substance/_version.py')

install_requires = ['setuptools>=1.1.3', 'PyYAML', 'tabulate', 'paramiko', 'netaddr', 'requests', 'tinydb', 'python_hosts==0.3.3', 'jinja2']

if 'Darwin' in platform.system():
  install_requires.append('macfsevents')

setup(name='substance',
      version=__version__,
      author='Turbulent',
      author_email='oss@turbulent.ca',
      license='Apache License 2.0',
      long_description=readme,
      description='Substance - Local dockerized development environment',
      install_requires=install_requires,
      packages=find_packages(),
      package_data={ 'substance': ['support/*'] },
      test_suite='tests',
      zip_safe=False,
      include_package_data=True,
      entry_points={
        'console_scripts': [
          'substance = substance.cli:cli',
          'subenv = substance.subenv.cli:cli'
        ],
      })
