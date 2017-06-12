![alt text](docs/source/_static/substance.png "substance")

Local Docker-powered development environments

# Overview

## Why?
Substance combines a virtual machine and docker into one self contained tool.
Complex projects can be distributed with a .substance folder which defines all
the environmental details in one so you can spend more time developing and less
time setting up servers.

## How
Substance is backed by Virtual Box, the docker engine and ``dockwrkr`` to
compose containers. With substance you create an `engine` which runs it's own
virtual machine with the docker daemon and synchronizes a `devroot` folder with
your project source code to the engine. Substance then allows you to switch
from project to project simply by having a simple `.substance` folder in the
root of your project source to define the containers and folders/volumes needed
to run your project.

## Documentation

For installation and usage, consult the [Substance
Documentation](http://doc.developers.turbulent.ca/substance/master/).

## License

All work found under this repository is licensed under the [Apache
License 2.0](LICENSE).

