# Substance usage & insallation (OSX)

## Installation

For Windows installation, see [INSTALL.windows.md](INSTALL.windows.md)

For macOS installation, see [INSTALL.macos.md](INSTALL.macos.md)

For Linux installation, see [INSTALL.linux.md](INSTALL.linux.md)

## Usage

### Create your first engine

To start using a substance environment, first create an engine. For the sake of this example we will create an engine named `work`.

```
substance engine create work --memory 2048 --cpus 2 --box turbulent/substance-box:0.6
```

Launch your engine with the launch command:

```
substance engine launch work
```
After a few minutes, substance will have pulled the box and launched your engine. By default substance will create a devroot directory for this new engine in `$HOME/substance/work`.

We need to tell substance to use our new engine as the default engine for substance commands. This is done with the `use` command:

```
substance use work
```

### Syncing local files to and from the engine

You can start the synch process like so:

```
substance sync
```

This will make sure all local files located under `~/substance/[engine name]` are kept in sync with the engine's local file system.

Always keep this process running while you develop! 

### Work on a project

To start working on a project, `git clone` the project in `~/substance/[engine name]/[project name]`. Make sure your files are properly sync'ed, then instruct substance to switch to that project and initialize the development environment by issuing the following command:

```
substance switch myprojectname
```

This will download the proper docker images and start the docker containers required for the project to work.

At this point, your environment is up-and-running, but the project may require further initialization steps. Check with your project lead for project-specific initialization steps.

### Consulting logs

To view logs of the various services of your environment:

```
substance logs [containername] [servicename]
```

This will automatically tail the logs matching the filters you provided. For example, `substance logs web php` will tail the PHP logs produced by the PHP-FPM process running in the `web` container.

## Updating substance to a new version

In the event that an update to the alpha is distributed, these commands will allow you to update the substance tools on your machine without losing data or engines.

```
pip uninstall subwatch
pip uninstall substance
pip install git+https://gitlab.turbulent.ca/bbeausej/subwatch.git@VERSION
pip install git+https://gitlab.turbulent.ca/bbeausej/substance.git@VERSION
```

## Setting up your project for substance

**Warning: Some of this information may be a little out-of-date. We will soon provide an automated tool to do this work. In the mean time, please talk to the substance developers directly if you want to setup your project for substance.**

At the top level of your project source code create a folder named ``.substance``. In this folder. A system to initialize projects is in the works, but for now create the following base structure or copy it from a recent project:

```
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
```

Ensure the `var` directory and it's children have mode 0777.

### Environment configuration

In your `.substance` folder you should create a `.env` file that will host the configuration/environment variable you will need when templating files in your project subenv.

The special variable called `SUBENV_FQDN` controls the DNS name for your project. Make sure you set it. Also, make sure this name is in the same TLD as configured in your substance config. (`~/.substance/subenv.yml`)

Here is a sample `.env` :
```
SUBENV_FQDN="myproject.dev"
MYCUSTOMVAR="foobar"
```

When resolving variables ; subenv will also look for a `.env` file at the root of your project for overrides.

### Configuring containers

Substance uses `dockwrkr` to manage containers in the work engine. Your project must define the containers it requires to function and their configuration in the form of a `dockwrkr.yml`` file.

Your `.substance` directory must contain a dockwrkr.yml.jinja that will be used by substance to resolve environment and configuration variable before writing the file in your project environment in the work engine.

Refer to the [dockwrkr](https://gitlab.turbulent.ca/turbulent/dockwrkr) manual for details on this configuration as well as the subenv command for details on the variables available. All variables you defined in your `.env` file can be used in the jinja template.

Here is a sample HEAP2 project dockwrkr configuration template:

```
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
 ```
