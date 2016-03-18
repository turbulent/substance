from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

version = '0.1'
install_requires = ['setuptools', 'PyYAML', 'tabulate']

setup(name='substance',
      version=version,
      author='turbulent/bbeausej',
      author_email='b@turbulent.ca',
      license='MIT',
      long_description=readme,
      description='substance - local dockerized development environment',
      install_requires=install_requires,
      packages=['substance'],
      test_suite='tests',
      entry_points={
        'console_scripts': [
          'substance = substance:cli',
        ],
      })
