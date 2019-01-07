from setuptools import setup, find_packages
import platform

with open('README.rst') as f:
    readme = f.read()

with open('substance/_version.py') as versionFile:
    exec(versionFile.read())

install_requires = [
    'setuptools>=1.1.3',
    'PyYAML',
    'tabulate',
    'paramiko>=2.3.1',
    'netaddr',
    'requests',
    'tinydb',
    'python_hosts==0.3.3',
    'jinja2'
]

if 'Darwin' in platform.system():
    install_requires.append('macfsevents')

setup(name='substance',
      version=__version__,
      author='Turbulent',
      author_email='oss@turbulent.ca',
      url='https://substance.readthedocs.io/',
      license='Apache License 2.0',
      long_description=readme,
      description='Substance - Local dockerized development environment',
      install_requires=install_requires,
      extras_require={
        ':sys.platform == "darwin"': ['macfsevents'],
        ':sys.platform == "linux"': ['watchdog']
      },
      python_requires='>=3',
      packages=find_packages(),
      package_data={'substance': ['support/*']},
      test_suite='tests',
      zip_safe=False,
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'substance = substance.cli:cli',
              'subenv = substance.subenv.cli:cli'
          ],
      })
