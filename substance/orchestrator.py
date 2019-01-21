from abc import (ABC, abstractmethod)
from substance.utils import (CommandList)


class Orchestrator(ABC):

    engine = None

    def __init__(self, engine):
        self.engine = engine
        super().__init__()

    def resetAll(self, time=10):
        return [
            "docker ps -q --filter 'label=ca.turbulent.dockwrkr.managed' | xargs -r docker rm -f",
            "docker ps -q --filter 'label=com.docker.compose.version' | xargs -r docker rm -f"
        ]

    @abstractmethod
    def startAll(self):
        pass

    @abstractmethod
    def restartAll(self, time=10):
        pass

    @abstractmethod
    def stopAll(self, time=10):
        pass

    @abstractmethod
    def removeAll(self, time=10):
        pass

    @abstractmethod
    def start(self, containers):
        pass

    @abstractmethod
    def stop(self, containers, time=10):
        pass

    @abstractmethod
    def remove(self, containers, time=10):
        pass

    @abstractmethod
    def restart(self, containers, time=10):
        pass

    @abstractmethod
    def exec(self, container, cmd, cwd=None, user=None):
        pass

    @abstractmethod
    def run(self, container, commands):
        pass

    @abstractmethod
    def status(self):
        pass


class Dockwrkr(Orchestrator):

    def login(self):
        return ["dockwrkr login"]

    def startAll(self):
        return ["dockwrkr start -a"]

    def restartAll(self, time=10):
        return ["dockwrkr restart -a -t %s" % (time)]

    def stopAll(self, time=10):
        return ["dockwrkr stop -a -t %s" % (time)]

    def removeAll(self, time=10):
        return ["dockwrkr remove -a -t %s" % (time)]

    def start(self, containers):
        return ["dockwrkr start %s" % (' '.join(containers))]

    def stop(self, containers, time=10):
        return ["dockwrkr stop %s -t %s" % (' '.join(containers), time)]

    def remove(self, container, time=10):
        return ["dockwrkr remove %s -t %s" % (' '.join(containers), time)]

    def restart(self, containers, time=10):
        return ["dockwrkr restart %s -t %s" % (' '.join(containers), time)]

    def recreate(self, containers, time=10):
        return ["dockwrkr recreate %s -t %s" % (' '.join(containers), time)]

    def exec(self, container, cmd, cwd=None, user=None):
        opts = []
        cmdline = ' '.join(cmd)
        initCommands = CommandList(['export TERM=xterm', cmdline])
        if user:
            opts.append('--user %s' % user)
        if cwd:
            initCommands.insert(0, 'cd %s' % cwd)

        tpl = {
            'opts': ' '.join(opts),
            'container': container,
            'initCommands': initCommands.logicAnd()
        }

        return ["dockwrkr exec -t -i %(opts)s %(container)s '/bin/sh -c \"%(initCommands)s\"'" % tpl]

    def run(self, task, args):
        return ["dockwrkr run %s %s" % (task, ' '.join(args))]

    def status(self):
        return ["dockwrkr status"]


class Compose(Orchestrator):

    def login(self):
        return []

    def startAll(self):
        return ["docker-compose up -d"]

    def restartAll(self, time=10):
        return ["docker-compose restart-t %s" % (time)]

    def stopAll(self, time=10):
        return ["docker-compose stop -t %s" % (time)]

    def removeAll(self, time=10):
        return ["docker-compose rm -f -s"]

    def start(self, containers):
        return ["dockwrkr start %s -d" % (' '.join(containers))]

    def stop(self, containers, time=10):
        return ["docker-compose stop %s -t %s" % (' '.join(containers), time)]

    def remove(self, container, time=10):
        return ["docker-compose rm -s -f %s" % (' '.join(containers))]

    def restart(self, containers, time=10):
        return ["docker-compose restart %s -t %s" % (' '.join(containers), time)]

    def recreate(self, containers, time=10):
        return ["(docker-compose rm -f -s %s && docker-compose start %s)" % (' '.join(containers), ' '.join(containers))]

    def exec(self, container, cmd, cwd=None, user=None):
        opts = []
        cmdline = ' '.join(cmd)
        initCommands = ['export TERM=xterm', cmdline]
        if user:
            opts.append('--user %s' % user)
        if cwd:
            initCommands.insert(0, 'cd %s' % cwd)

        tpl = {
            'opts': ' '.join(opts),
            'container': container,
            'initCommands': ' && '.join(initCommands)
        }

        return ["docker-compose exec %(opts)s %(container)s /bin/sh -c \"%(initCommands)s\"" % tpl]

    def run(self, task, args):
        return ["docker-compose run %s %s" % (task, ' '.join(args))]

    def status(self):
        return ["docker-compose ps"]
