# substance

Local docker-powered development environments

# Overview

substance is a integrated tool for defining and running a multi-continer docker development environments. With substance you create an `engine` which runs it's own virtual machine with the docker daemon and synchronizes a `devroot` folder with your project source code to the engine. 

substance then allows you to switch from project to project simply by having a simple `.substance` folder in the root of your project source to define the containers and folders/volumes needed to run your project.

# Engine commands

- [x] substance engine ls
- [x] substance engine init
- [x] substance engine delete
- [x] substance engine launch
- [x] substance engine stop
- [x] substance engine suspend
- [x] substance engine deprovision
- [x] substance engine ssh
- [x] substance engine sshinfo
- [x] substance engine env

- [x] substance help


# Utility

- [ ] substance use enginename
- [x] substance switch project [--restart]
- [x] substance status [--full]
substance logs -f web*nginx*access*.log -n 100
substance docker command

# Project commands

- [x] substance start [-e ENGINE] [CONTAINER...] --reset
- [x] substance stop [-e ENGINE] [CONTAINER...] 
substance enter CONTAINER
substance exec CONTAINER command...

- [ ] Porcelain spawn
- [ ] Porcelain hatch

# TODO

- [ ] Doc: How it works
- [ ] Doc: How to use
- [ ] Doc: Box guide
- [ ] Speed-up import @ python start
- [ ] Refactor CLI with functional