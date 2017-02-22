
![alt text](docs/substance.png "substance")

Local docker-powered development environments

# Overview

## Why?
Substance combines a virtual machine and docker into one self contained tool. Complex projects can be distributed with a .substance folder which defines all the environmental details in one so you can spend more time developing and less time setting up servers.

## How
Substance is backed by Virtual Box, the docker engine and ``dockwrkr`` to compose containers. With substance you create an `engine` which runs it's own virtual machine with the docker daemon and synchronizes a `devroot` folder with your project source code to the engine. Substance then allows you to switch from project to project simply by having a simple `.substance` folder in the root of your project source to define the containers and folders/volumes needed to run your project.

## Installation

For Windows installation, see [INSTALL.windows.md](docs/INSTALL.windows.md)

For macOS installation, see [INSTALL.macos.md](docs/INSTALL.macos.md)

For Linux installation, see [INSTALL.linux.md](docs/INSTALL.linux.md)

# Usage

See [USAGE.md](docs/USAGE.md) on how to use substance.

# subenv

The command line program ``subenv`` (installed with substance) allows manipulating container environments in your project. 

You should not have to use `subenv` directly unless you are messing around inside your engine's virtual machine. Just stick to `substance` for day-to-day use.

If you are curious about how substance manages your projects within the VM, however, you can read more about `subenv` here: [subenv.md](docs/subenv.md).

