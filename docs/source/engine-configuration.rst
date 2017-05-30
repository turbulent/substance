Engine Configuration
====================

Substance engines are defined by a simple YAML configuration file which is
located at ``$_HOME/.substance/engines/[enginename]/engine.yml``. This file is
automatically created for you when you create a new engine using the
``substance engine create`` command.

You can edit this file in any text editor of your choice. As a convenience,
Substance will open it in your favorite editor (specified by the ``EDITOR``
environment variable) using the command ``substance engine edit [enginename]``.

What follows is an overview of all configuration sections in the file.

``box``
-------

Specifies the box file used to create the VM in VirtualBox upon first launch.
After first launch, this setting is no longer used.

``devroot``
-----------

This configures how the local directory for the engine will behave.

* ``path`` specifies the path to the directory on the local machine.
* ``mode`` specifies the sync mode. Possible values are ``unison`` (default)
  and ``subwatch`` (deprecated).
* ``excludes`` lists filename patterns to ignore on sync. You can use this
  setting to ignore additional file patterns for the projects hosted using this
  engine. Note that this can only match patterns based on filename, not full
  directory path. To ignore files based on directory path, use the ``syncArgs``
  setting.
* ``syncArgs`` lists additional arguments to pass to ``unison`` when ``mode`` is set
  to ``unison``.

``docker``
----------

This configures the Docker daemon running inside the engine. You will usually
want to leave the defaults as-is.

``driver``
----------

Specifies the virtualization backend to use for managing the virtual machine.
``virtualbox`` is the only currently-supported value for now, but more backends
will be added in the future.

``network``
-----------

All Substance engines are networked using a Host-only network adapter serving
as a DHCP server. The settings in this section are automatically filled in and
updated by Substance after each launch of the engine.

``profile``
-----------

Specifies the capabilities of the virtual machine. Currently, two settings are
supported:

* ``cpus``: Specifies number of virtual CPUs
* ``memory``: Specifies amount of memory to reserve for the VM (in megabytes)

Note that these settings can be changed even after the VM has been created in
VirtualBox (requires a reboot of the VM).

.. _aliases:

``aliases``
-----------

Substance engines can define a list of commonly-used commands to execute within
specific containers. This allows the user to avoid having to type a long and
difficult-to-remember command for common tasks such as building a website,
pulling packages, etc.

Since Substance was designed for web development first, all engines come
pre-configured with a few aliases for web development. All of these aliases are
configured to be executed within a container named ``web`` as a user named
``heap`` within the directory ``/vol/website``:

* ``substance make``: Execute ``make``.
* ``substance composer``: Execute the ``composer`` command (PHP package
  manager).
* ``substance npm``: Execute the ``npm`` command (Javascript package manager)
* ``substance watch``: Execute the ``webpack -w`` command (Web build tool in
  watch mode)

Note that executing an alias will pass along all arguments following the name
of the alias, e.g.::

  $ substance make clean TARGETS=all # executes 'make clean TARGETS=all' within the container

You can add more aliases (or even change the configuration for the
pre-configured ones) by editing your engine's definition file. Here's the
example configuration for the above command:

.. code-block:: yaml

   aliases:
     composer:
       args:
       - composer
       container: web
       cwd: /vol/website
       user: heap
     make:
       args:
       - make
       container: web
       cwd: /vol/website
       user: heap
     npm:
       args:
       - npm
       container: web
       cwd: /vol/website
       user: heap
     watch:
       args:
       - watch
       container: web
       cwd: /vol/website
       user: heap

Simply add more entries to the ``aliases`` YAML object to define new aliases
for your engine.
