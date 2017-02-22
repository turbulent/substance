# The `subenv` utility

``subenv`` can read the spec folder ``.substance.`` in your project root and will template and create the runtime environment to run your project.

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

