from setuptools import setup, find_packages
import platform

with open('README.rst') as f:
    readme = f.read()

exec(open('substance/_version.py').read())

install_requires = ['setuptools>=1.1.3', 'PyYAML', 'tabulate', 'paramiko', 'netaddr', 'requests', 'tinydb', 'python_hosts==0.3.3', 'jinja2', 'future']

if 'Darwin' in platform.system():
  install_requires.append('macfsevents')

setup(name='substance',
      version=__version__,
      author='turbulent/bbeausej',
      author_email='b@turbulent.ca',
      license='MIT',
      long_description=readme,
      description='substance - local dockerized development environment',
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
