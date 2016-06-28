
![alt text](docs/substance.png "substance")

Local docker-powered development environments

# Overview

substance is a integrated tool for defining and running a multi-continer docker development environments. It is backed by Virtual Box, the docker engine and ``dockwrkr`` to compose containers.

With substance you create an `engine` which runs it's own virtual machine with the docker daemon and synchronizes a `devroot` folder with your project source code to the engine. 

substance then allows you to switch from project to project simply by having a simple `.substance` folder in the root of your project source to define the containers and folders/volumes needed to run your project.

# Engine commands

- [x] substance engine ls
- [x] substance engine init
- [x] substance engine delete
- [x] substance engine launch
- [x] substance engine halt [--force]
- [x] substance engine suspend
- [x] substance engine deprovision
- [x] substance engine ssh
- [x] substance engine sshinfo
- [x] substance engine env

# Usage

- [x] substance help
- [x] substance use enginename --env projectA
- [x] substance switch project [--restart]
- [x] substance status [--full]
- [x] substance logs -f web*nginx*access*.log -n 100
- [x] substance docker command

# Project commands

- [x] substance start [-e ENGINE] [CONTAINER...] --reset
- [x] substance stop [-e ENGINE] [CONTAINER...] 
- [x] substance enter CONTAINER
- [x] substance exec CONTAINER command...

# subenv

The command line program ``subenv`` (installed with substance) allows to manipulate container environments in your project. ``subenv`` can read the spec folder ``.substance.`` in your project root and will template and create the runtime environment to run your project.

When operating on a substance engine, the subenv utility is used on the engine machine to generate and switch between project environments.

## subenv commands

```
  help                Print help for a specific substance command
  ls                  Print a list of substance project environments.
  init                Initialize or apply a project environment
  delete              Permanently delete a project environment
  use                 Set a project environment as current
  current             Print the current subenv on stdout
  run                 Run a command in the current subenv directory
  vars                Output the vars for an env on stdout, optionally filtered
```

## subenv quick how-to

You initiate/apply an environment by using the ``init`` command:

```
> subenv init path/to/myprojectA
Initializing subenv from: path/to/projectA
Loading dotenv file: 'path/to/projectA/.substance/.env'
Loading dotenv file: 'path/to/devroot/projectA/.env'
Applying environment to: /substance/envs/projectA
Environment 'projectA' initialized.
```

List available environments using ``ls`` command:

```
> subenv ls

NAME         CURRENT    BASEPATH                        MODIFIED
projectA     X          /substance/devroot/projectA  June 28 2016, 14:14:17
projectB     X          /substance/devroot/projectB  June 28 2016, 15:11:10
projectC     X          /substance/devroot/projectC  June 23 2016, 01:33:02
```

Switch the currently use environment with ``use``:

```subenv use projectC```

View the currently in use environment with ``current``:

```
> subenv current
projectC
```

View the computed variables for the current env:

```
> subenv vars
name="projectA"
fqdn="projectA.dev"
```


## Creating a subenv spec (.substance)

Each folder in your engine devroot (referred to as a project) must have a spec directory (.substance) to define what the environment needed to run the project is.

When a specdir is applied (using ``init``) subenv will go through the file structure of the specdir and take the following actions:

- Each file is copied to the environment path
- Each folder is created recursively in the environment path
- All files ending with ``.jinja`` are render with Jinja2 and installed in the environment path withouth the .jinja extension.

The variable context for the jinja templates is populated from the merge ``dotenv`` (.env) files in the specdir and the project directory. subenv will load the .env file in your specdir first and override the values from an optional .env file in your project root.

Additionally, subenv will provide the following variables:


| Variable            | Value                                          |
| ------------------- | ---------------------------------------------- |
| SUBENV_NAME         | Name of the subenv                               |
| SUBENV_LASTAPPLIED  | Epoch time of last time this env was applied   |
| SUBENV_SPECPATH     | Full path to the specdir                       |
| SUBENV_BASEPATH     | Full path to the project path                  |
| SUBENV_ENVPATH      | Full path to the environment                   |
| SUBENV_VARS         | Dict of all variables                          |


# TODO

- [x] P1 Support subenv FQDN to /etc/hosts
- [ ] P1 validate, test and fix Windows support
- [x] P1 Auto-create engine devroot on init
- [x] Fix subprogram help (substance help engine ls)
- [x] Don't initialize core manually in each command
- [ ] Handle substance version
- [ ] Porcelain spawn
- [ ] Porcelain hatch
- [ ] Doc: How it works
- [ ] Doc: How to use
- [ ] Doc: Box guide
- [ ] Box service
- [ ] Box push/pull commands
- [ ] Box: ensure paravirt network

## Bugs

- [ ] BUG substance docker/enter/exec -e conflicts
- [ ] BUG Sync: Ignore backdraft events when synching (esp git manips)


## Improvements

- [ ] dotenv parsing should support "export", multiline and enforce caps.
- [ ] Refactor lists to use * to display 'current' in subenv. 
- [ ] NTH Use ssh binary instead of Paramiko for Link. (w/ ControlPersist)
- [ ] NTH Rework the hosts file mgmt. module sucks.
- [ ] NTH Speed-up import @ python start
- [ ] NTH Refactor CLI with functional