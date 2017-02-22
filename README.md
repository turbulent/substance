
![alt text](docs/substance.png "substance")

Local docker-powered development environments

# Overview

## Why?
Substance combines a virtual machine and docker into one self contained tool. Complex projects can be distributed with a .substance folder which defines all the environmental details in one so you can spend more time developing and less time setting up servers.

## How
Substance is backed by Virtual Box, the docker engine and ``dockwrkr`` to compose containers. With substance you create an `engine` which runs it's own virtual machine with the docker daemon and synchronizes a `devroot` folder with your project source code to the engine. Substance then allows you to switch from project to project simply by having a simple `.substance` folder in the root of your project source to define the containers and folders/volumes needed to run your project.

# Commands

```
  help                Print help for a specific substance command
  use                 Specify which engine is used by default
  launch              Launch the current engine's virtual machine
  suspend             Suspend the current engine's virtual machine
  halt                Suspend the current engine's virtual machine
  switch              Switch the active subenv for an engine
  start               Start all or specific container(s)
  stop                Stop all or specific container(s)
  restart             Restart all or specified container(s)
  recreate            Recreate all or specified container(s)
  ssh                 Connect using SSH to the engine or directly into a container by appending the container name
  status              Show substance engine and env status
  logs                Display current subenv logs
  sync                Synchronize & watch the devroot of the current engine
  engine              Substance engine management
  box                 Substance box management
```

# Engine commands

```
  ls                  List substance engines
  init                Initialize a new engine configuration
  delete              Permanently delete an engine and it's associated machine.
  launch              Launch an engine's virtual machine
  halt                Halt an engine's vm gracefully or forcefully.
  suspend             Suspend an engine gracefully.
  deprovision         Destroy an engine's associated virtual machine
  edit                Edit an engine configuration
  ssh                 Connect using SSH to the engine's virtual machine.
  env                 Print the shell variables to set up the local docker client environment
  sshinfo             Obtain the ssh info configuration for connecting to an engine
  sync                Synchronize and watch the devroot folder for an engine
```

# Box commands

```
  help                Print help for a specific substance command
  ls                  List substance box available locally
  pull                Download a box
  delete              Permanently delete a box.
```

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

### subenv.yml

You can also create a `subenv.yml` file to specify additional commands to be executed once the environment is applied. The file format is YAML and only the `script` key is available which should contain a list of shell commands to run when applying the envrionment. Each command is run as substance relatively in the environment directory.

Sample:

```
script:
  - chmod -R 777 var
  - chmod -R 700 database
```

# Setup

[docs/USAGE.md](USAGE.md)
