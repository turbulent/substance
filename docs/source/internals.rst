Substance Internals
===================

The following documentation is not required knowledge for using Substance.
However, if you are curious about how Substance works under-the-hood, keep
reading!

The ``subenv`` utility
----------------------

When operating on a substance engine, the ``subenv`` utility is used inside the
engine virtual machine to generate and switch between project environments.

``subenv`` can read the spec folder ``.substance``. in your project root and
will template and create the runtime environment to run your project.

How to use ``subenv``
---------------------

You initiate/apply an environment by using the ``init`` command::

  $ subenv init path/to/myprojectA
  Initializing subenv from: path/to/projectA
  Loading dotenv file: 'path/to/projectA/.substance/.env'
  Loading dotenv file: 'path/to/devroot/projectA/.env'
  Applying environment to: /substance/envs/projectA
  Environment 'projectA' initialized.

List available environments using ``ls`` command::

  $ subenv ls

  NAME         CURRENT    BASEPATH                        MODIFIED
  projectA     X          /substance/devroot/projectA     June 28 2016, 14:14:17
  projectB     X          /substance/devroot/projectB     June 28 2016, 15:11:10
  projectC     X          /substance/devroot/projectC     June 23 2016, 01:33:02

Switch the currently use environment with ``use``::

  $ subenv use projectC

View the currently in use environment with ``current``::

  $ subenv current
  projectC

View the computed variables for the current environment::

  $ subenv vars
  name="projectA"
  fqdn="projectA.local.dev"

Creating a subenv spec (.substance)
-----------------------------------

Each directory in your engine devroot (referred to here as a project) must have
a spec directory (.substance) to define what the environment needed to run the
project is.

When a specdir is applied (using ``init``) subenv will go through the file
structure of the specdir and take the following actions:

- Each file is copied to the environment path
- Each folder is created recursively in the environment path
- All files ending with ``.jinja`` are render with Jinja2 and installed in the
  environment path withouth the .jinja extension.

The variable context for the jinja templates is populated from the merge
``.env`` files in the specdir and the project directory. ``subenv`` will load
the ``.env`` file in your specdir first and override the values from an optional
``.env`` file in your project root.

Additionally, subenv will provide the following variables for use in your jinja
templates:

====================== ============================================
Variable               Value                                       
====================== ============================================
``SUBENV_NAME``        Name of the subenv                          
``SUBENV_LASTAPPLIED`` Epoch time of last time this env was applied
``SUBENV_SPECPATH``    Full path to the specdir                    
``SUBENV_BASEPATH``    Full path to the project path               
``SUBENV_ENVPATH``     Full path to the environment                
``SUBENV_VARS``        Dict of all variables                       
====================== ============================================

``subenv.yml``
--------------

You can also create a ``subenv.yml`` file to specify additional commands to be
executed once the environment is applied. The file format is YAML and only the
``script`` setting is available which should contain a list of shell commands to
run when applying the envrionment. Each command is run as UID 1000 within the
environment directory.

Sample:

.. code-block:: yaml

   script:
     - chmod -R 777 var
     - chmod -R 700 database

