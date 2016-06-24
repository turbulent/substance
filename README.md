# substance

Local docker-powered development environments

# Overview

substance is a integrated tool for defining and running a multi-continer docker development environments. With substance you create an `engine` which runs it's own virtual machine with the docker daemon and synchronizes a `devroot` folder with your project source code to the engine. 

substance then allows you to switch from project to project simply by having a simple `.substance` folder in the root of your project source to define the containers and folders/volumes needed to run your project.

# Engine commands

substance engine ls
substance engine init
substance engine delete
substance engine launch
substance engine stop
substance engine suspend
substance engine deprovision
substance engine ssh
substance engine sshinfo
substance engine env

substance help


# Utility

x substance use enginename project
x substance switch project --restart
substance status
substance logs -f web*nginx*access*.log -n 100
substance docker command

# Project commands

substance start -a
substance start container
substance stop container

substance enter container
substance exec container command