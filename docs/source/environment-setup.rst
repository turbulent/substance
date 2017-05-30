Environment Setup
=================

.. warning::

   Some of this information may be a little out-of-date. We will soon provide
   an automated tool to do this work. In the mean time, please talk to the
   substance developers directly if you want to setup your project for
   substance.

At the top level of your project source code create a folder named ``.substance``. In this folder. A system to initialize projects is in the works, but for now create the following base structure or copy it from a recent project:

.. code-block:: text

   .
   |-- conf
   |   |-- cron
   |   |-- logrotate
   |   `-- web
   |-- data
   |   |-- media
   |   |-- uploads
   |   `-- work
   |-- database
   |-- dockwrkr.yml.jinja
   |-- logs
   |-- spool
   |-- subenv.yml
   `-- var
       |-- heap
       |   `-- cache
       |-- purifier
       |   `-- cache
       `-- smarty
           `-- compile

Ensure the ``var`` directory and it's children have mode 0777.

Environment configuration
-------------------------

In your ``.substance`` folder you should create a ``.env`` file that will host
the configuration/environment variable you will need when templating files in
your project subenv.

The special variable called ``SUBENV_FQDN`` controls the DNS name for your
project. Make sure you set it. Also, make sure this name is in the same TLD as
configured in your substance config. (``~/.substance/subenv.yml``)

Here is a sample ``.env``::

  SUBENV_FQDN="myproject.local.dev"
  MYCUSTOMVAR="foobar"

When resolving variables ; subenv will also look for a ``.env`` file at the
root of your project for overrides.

Configuring containers
----------------------

Substance uses `dockwrkr`_ to manage containers in the work engine. Your
project must define the containers it requires to function and their
configuration in the form of a ``dockwrkr.yml`` file.

Your ``.substance`` directory must contain a ``dockwrkr.yml.jinja`` that will
be used by substance to resolve environment and configuration variable before
writing the file in your project environment in the work engine.

Refer to the `dockwrkr`_ manual for details on this configuration as well as
the subenv command for details on the variables available. All variables you
defined in your ``.env`` file can be used in the jinja template.

Here is a sample Heap project ``dockwrkr`` configuration template

.. code-block:: yaml

    pids:
      enabled: false
      dirs: pids
    containers:
      dbmaster:
        image: docker-registry.turbulent.ca:5000/heap-mysql:2.0
        hostname: dbmaster
        env:
          VAR_MYSQL_PASS: "dev"
          VAR_MYSQL_INNODB_BUFFER_POOL_SIZE: "100M"
          VAR_MYSQL_SERVER_ID: 2
          VAR_MYSQL_REPLICATION_MASTER: 1
          VAR_MYSQL_REPLICATION_USER: "replication"
          VAR_MYSQL_REPLICATION_PASSWORD: "dev"
          VAR_PROJECT_NAME: {{name}}
        publish:
          - "3306:3306"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/database:/vol/database"

      cache:
        image: docker-registry.turbulent.ca:5000/heap-memcached:2.0
        hostname: cache
        publish:
          - "11211:11211"
        env:
          VAR_MEMCACHED_SIZE: "64M"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"

      redis:
        image: docker-registry.turbulent.ca:5000/heap-redis:2.0
        hostname: redis
        publish:
          - "6379:6379"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/database:/vol/database"

      qmgr:
        image: docker-registry.turbulent.ca:5000/heap-qmgr:2.0.1
        hostname: qmgr
        env:
          VAR_HEAP_QUEUE_WORKERS: 1
        link:
          - "dbmaster:dbmaster"
          - "cache:cache"
          - "sessions:sessions"
          - "rabbit:rabbit"
          - "redis:redis"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/var:/vol/var"
          - "{{SUBENV_ENVPATH}}/spool:/vol/spool"
          - "{{SUBENV_BASEPATH}}:/vol/website"
          - "{{SUBENV_ENVPATH}}/data:/vol/data"

      web:
        image: docker-registry.turbulent.ca:5000/heap-app-dev:2.0.5
        hostname: web
        env:
          VAR_NMAILER_HOSTNAME: ""
          VAR_NMAILER_ROOT_ALIAS: ""
          VAR_NMAILER_DOMAIN: ""
          VAR_NMAILER_REMOTE_TLS: 0
          VAR_NMAILER_REMOTE_HOST: ""
          VAR_NMAILER_REMOTE_PORT: "25"
          VAR_NMAILER_REMOTE_USER: ""
          VAR_NMAILER_REMOTE_PASS: ""
          VAR_NGINX_SERVER_NAME: "{{SUBENV_FQDN}}"
          VAR_FPM_MAX_CHILDREN: 5
          VAR_FPM_MIN_CHILDREN: 5
          VAR_FPM_MAX_REQUESTS: 500
        link:
          - "dbmaster:dbmaster"
          - "cache:cache"
          - "sessions:sessions"
          - "rabbit:rabbit"
          - "redis:redis"
        publish:
          - "80:80"
          - "443:443"
          - "9001:9001"
          - "9002:9002"
          - "9003:9003"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/var:/vol/var"
          - "{{SUBENV_ENVPATH}}/spool:/vol/spool"
          - "{{SUBENV_ENVPATH}}/data:/vol/data"
          - "{{SUBENV_ENVPATH}}/conf/web:/vol/conf"
          - "{{SUBENV_BASEPATH}}:/vol/website"

      cron:
        image: docker-registry.turbulent.ca:5000/heap-cron:2.0.1
        hostname: cron
        env:
          VAR_NMAILER_HOSTNAME: ""
          VAR_NMAILER_ROOT_ALIAS: ""
          VAR_NMAILER_DOMAIN: ""
          VAR_NMAILER_REMOTE_TLS: 0
          VAR_NMAILER_REMOTE_HOST: ""
          VAR_NMAILER_REMOTE_PORT: "25"
          VAR_NMAILER_REMOTE_USER: ""
          VAR_NMAILER_REMOTE_PASS: ""
        link:
          - "dbmaster:dbmaster"
          - "cache:cache"
          - "sessions:sessions"
          - "rabbit:rabbit"
          - "redis:redis"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/var:/vol/var"
          - "{{SUBENV_ENVPATH}}/spool:/vol/spool"
          - "{{SUBENV_ENVPATH}}/conf/cron:/vol/conf"
          - "{{SUBENV_ENVPATH}}/data:/vol/data"
          - "{{SUBENV_BASEPATH}}:/vol/website"

      logrotate:
        image: docker-registry.turbulent.ca:5000/heap-logrotate:2.0
        hostname: logrotate
        env:
          VAR_LOGROTATE_MODE: "daily"
          VAR_LOGROTATE_ROTATE: "7"
        volume:
          - "{{SUBENV_ENVPATH}}/logs:/vol/logs"
          - "{{SUBENV_ENVPATH}}/conf/logrotate:/vol/conf"
          - "/var/lib/docker/containers:/vol/docker-logs"

.. _dockwrkr: https://github.com/bbeausej/dockwrkr

