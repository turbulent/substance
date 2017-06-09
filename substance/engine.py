from __future__ import print_function
from builtins import str
from builtins import map
from builtins import object
import os
import socket
import logging
from contextlib import closing
from collections import (OrderedDict, namedtuple)
import substance.core
from substance.monads import *
from substance.config import (Config)
from substance.logs import *
from substance.shell import Shell
from substance.link import Link
from substance.box import Box
from substance.utils import mergeDict, parseDotEnv
from substance.hosts import SubHosts
from substance.driver.virtualbox import VirtualBoxDriver
from substance.constants import (EngineStates)
from substance.exceptions import (
  FileSystemError, 
  ConfigValidationError,
  EngineAlreadyRunning, 
  EngineNotRunning,
  EngineExistsError, 
  EngineNotProvisioned,
  EngineProvisioned,
  EnvNotDefinedError
)

logger = logging.getLogger(__name__)

class EngineProfile(object):
  def __init__(self, cpus=2, memory=1024):
    self.cpus = cpus
    self.memory = memory

  def __repr__(self):
    return "%s" % {'cpus': self.cpus, 'memory': self.memory}


class EngineFolder(object):
  def __init__(self, name, mode, hostPath, guestPath, uid=None, gid=None, umask=None, excludes=[], syncArgs=[]):
    self.name = name
    self.mode = mode
    self.hostPath = hostPath
    self.guestPath = guestPath
    self.uid = uid if uid else 1000
    self.gid = gid if gid else 1000
    self.umask = umask if umask else "0022"
    self.excludes = excludes
    self.syncArgs = syncArgs

 
  def setExcludes(self, exs=[]):
    self.excludes = exs

  def getExcludes(self):
    return self.excludes

  def __eq__(self, other):
    return True if self.__hash__() == other.__hash__() else False

  def __hash__(self):
    return hash((self.name, self.hostPath, self.guestPath))

  def __repr__(self):
    return "EngineFolder(name=%(name)s, %(mode)s host:%(hostPath)s -> guest:%(guestPath)s)" % self.__dict__


class Engine(object):

  def __init__(self, name, enginePath, core):
    self.name = name
    self.enginePath = enginePath
    self.core = core
    self.link = None
    configFile = os.path.join(self.enginePath, "engine.yml")
    self.config = Config(configFile)
    self.logAdapter = EngineLogAdapter(logger, self.__dict__)
    self.currentEnv = None

  def getDefaults(self):
    defaults = OrderedDict()
    defaults['name'] = 'default'
    defaults['driver'] = 'virtualbox'
    defaults['id'] = None
    defaults['box'] = 'turbulent/substance-box:0.6'
    defaults['profile'] = EngineProfile().__dict__
    defaults['docker'] = OrderedDict()
    defaults['docker']['port'] = 2375
    defaults['docker']['tls'] = False
    defaults['docker']['certificateFile'] = None
    defaults['network'] = OrderedDict() 
    defaults['network']['privateIP'] = None
    defaults['network']['publicIP'] = None
    defaults['network']['sshIP'] = None
    defaults['network']['sshPort'] = 4500
    defaults['devroot'] = OrderedDict()
    defaults['devroot']['path'] = os.path.join('~','devroot')
    defaults['devroot']['mode'] = 'unison'
    defaults['devroot']['syncArgs'] = [
      '-ignore', 'Path */var',
      '-ignore', 'Path */data'
    ]
    defaults['devroot']['excludes'] = [
      '{.*,*}.sw[pon]',
      '.bash*',
      '.composer',
      '.git',
      '.idea',
      '.npm',
      '.ssh',
      '.viminfo'
    ]
    aliases = [ 'make', 'composer', 'npm', 'heap', 'watch' ]
    defaults['aliases'] = { alias: { 'container': 'web', 'user': 'heap', 'cwd': '/vol/website', 'args': [alias] } for alias in aliases }
    defaults['aliases']['watch']['container'] = 'devs'
    defaults['aliases']['heap']['args'][0] = 'vendor/bin/heap'

    return defaults
  
  def validateConfig(self, config):
    fields = ['name','driver','profile','docker','network','devroot','box']

    ops = []
    ops.append(self.config.validateFieldsPresent(config.getConfig(), fields))
    ops.append(self.confValidateName(config.get('name', None)))
    ops.append(self.core.validateDriver(config.get('driver', None)))
    ops.append(self.confValidateDevroot(config.get('devroot', {})))

    def dd(err):
      print("%s" % err)
      return ConfigValidationError(err.message)

    return Try.sequence(ops) \
      .catch(dd) \
      .then(lambda: OK(config.getConfig()))

  def confValidateName(self, name):
    if name != self.name:
      return Fail(ConfigValidationError("Invalid name property in configuration (got %s expected %s)" %(config.get('name'), self.name))) 
    return OK(name)

  def confValidateDevroot(self, devroot):
    path = devroot.get('path', '')
    path = os.path.expanduser(path)
    if not path:
      return Fail(ConfigValidationError("devroot path configuration is missing."))
    elif not os.path.isdir(path):
      self.logAdapter.info("WARNING: devroot '%s' does not exist locally." % path)

    mode = devroot.get('mode', None)
    if not mode:
      return Fail(ConfigValidationError("devroot mode is not set."))
    elif mode not in ['sharedfolder','rsync','unison']:
      #XXX Fix hardcoded values.
      return Fail(ConfigValidationError("devroot mode '%s' is not valid." % mode)) 

    return OK(devroot)

  def getName(self):
    return self.name

  def getID(self):
    return self.config.id

  def getEnginePath(self):
    return self.enginePath

  def getEngineFilePath(self, fileName):
    return os.path.join(self.enginePath, fileName)

  def getDockerURL(self):
    if self.getDriverID():
      return "tcp://%s:%s" % (self.getPublicIP(), self.getDockerPort())
 
  def getDockerPort(self):
    return self.config.get('docker', {}).get('port', 2375) 

  def getDockerEnv(self):
    env = OrderedDict()
    #env['DOCKER_API_VERSION'] = '1.19'
    env['DOCKER_HOST'] = self.getDockerURL()
    env['DOCKER_TLS_VERIFY'] = ''
    return env

  def getPublicIP(self):
    return self.config.get('network').get('publicIP', None)

  def getPrivateIP(self):
    return self.config.get('network').get('privateIP', None)

  def getDriver(self):
    return self.core.getDriver(self.config.get('driver'))

  def getEngineProfile(self):
    profile = self.config.get('profile', {})
    return EngineProfile(**profile)

  def getDriverID(self):
    return self.config.get('id', None)

  def setDriverID(self, driverID):
    self.config.set('id', driverID)
    return OK(self)

  def getSSHPort(self):
    return self.config.getBlockKey('network', 'sshPort', 22)

  def getSSHIP(self):
    return self.config.getBlockKey('network', 'sshIP', 'localhost')

  def getConnectInfo(self):
    info = {
      'hostname': self.getSSHIP(),
      'port': self.getSSHPort()
    }
    return info

  def getDNSName(self):
    tld = self.core.config.get('tld')
    return self.name + tld

  def getSyncher(self):
    syncMode = self.config.get('devroot').get('mode')
    keyfile = self.core.getSSHPrivateKey()
    if keyfile.isFail():
      return keyfile
    if syncMode == 'rsync':
      from substance.syncher.rsync import SubwatchSyncher
      return SubwatchSyncher(engine=self, keyfile=keyfile.getOK())
    elif syncMode == 'unison':
      from substance.syncher.unison import UnisonSyncher
      return UnisonSyncher(engine=self, keyfile=keyfile.getOK())
    else:
      raise NotImplementedError()
    
  def clearDriverID(self):
    self.config.set('id', None)
    return OK(self)

  def loadConfigFile(self):
    return self.config.loadConfigFile().bind(self.validateConfig).map(self.chainSelf)

  def loadState(self):
    ddebug("Engine load state %s" % self.name)
    return self.fetchState().bind(self.setState).map(self.chainSelf)

  def setState(self, state):
    self.state = state
    return OK(None)

  def create(self, config=None, profile=None):
    if os.path.isdir(self.enginePath):
      return Fail(EngineExistsError("Engine \"%s\" already exists." % self.name))

    return Shell.makeDirectory(self.enginePath) \
      .then(defer(self.makeDefaultConfig, config=config, profile=profile)) \
      .bind(self.__ensureDevroot) \
      .bind(self.validateConfig) \
      .then(self.config.saveConfig) \
      .bind(dinfo("Generated default engine configuration in %s", self.config.configFile)) \
      .map(self.chainSelf)

  def __ensureDevroot(self, config):
    devroot = os.path.expanduser(config.get('devroot', {}).get('path'))
    if not os.path.isdir(devroot):
      self.logAdapter.info("Creating devroot at %s" % devroot)
      return Shell.makeDirectory(devroot).then(lambda: OK(config))
    return OK(config)
 
  def remove(self):
    if not os.path.isdir(self.enginePath):
      return Fail(FileSystemError("Engine \"%s\" does not exist." % self.name))
    if self.isProvisioned():
      return Fail(EngineProvisioned("Engine \"%s\" is provisioned." % self.name))
    return Shell.nukeDirectory(self.enginePath)
 
  def makeDefaultConfig(self, config=None, profile=None):
    default = self.getDefaults()
    default["name"] = self.name
    default["devroot"]["path"] = os.path.join(self.core.config.get('devroot'), self.name)

    cf = {}
    mergeDict(cf, default)
    mergeDict(cf, config)

    if profile:
      cf['profile']['cpus'] = profile.cpus
      cf['profile']['memory'] = profile.memory

    for ck, cv in cf.items():
      self.config.set(ck, cv)

    return OK(self.config)

  def getProfile(self):
    prof = self.config.get('profile', {})
    return EngineProfile(prof.get('cpus'), prof.get('memory'))

  def isProvisioned(self):
    '''
    Check that this engine has an attached Virtual Machine.
    '''
    return True if self.getDriverID() else False

  def validateProvision(self):
    '''
    Check that the provision attached to this engine is valid in the driver.
    ''' 
    if not self.isProvisioned():
      return OK(False)

    machID = self.getDriverID()
    return self.getDriver().exists(machID)

  def isRunning(self):
    return self.fetchState().map(lambda state: (state is EngineStates.RUNNING))

  def isSuspended(self):
    return self.fetchState().map(lambda state: (state is EngineStates.SUSPENDED))

  def fetchState(self):
    if not self.isProvisioned():
      return OK(EngineStates.INEXISTENT)
    return self.getDriver().getMachineState(self.getDriverID())
   
  def launch(self):
    '''
    # 1. Check that we know about a provisioned machined for this engine. Provision if not.
    # 2. Validate that the machine we know about is still provisioned. Provision if not.
    # 3. Check the machine state, boot accordingly
    # 4. Setup guest networking
    # 4. Fetch the guest IP from the machine and store it in the machine state.
    '''
    return self.provision() \
      .then(self.start) \
      .then(self.updateNetworkInfo) \
      .then(self.addToHostsFile) \
      .then(self.envLoadCurrent) \
      .catchError(EnvNotDefinedError, lambda e: OK(None)) \
      .then(dinfo("Engine \"%s\" has been launched.", self.name)) \
      .then(self.envStart if self.currentEnv else lambda: OK(None))

  def addToHostsFile(self):
    self.logAdapter.info("Registering engine as '%s' in local hosts file" % self.getDNSName())
    return SubHosts.register(self.getDNSName(), self.getPublicIP())
    
  def removeFromHostsFile(self):
    self.logAdapter.info("Removing engine from local hosts file")
    return SubHosts.unregister(self.getDNSName())

  def updateNetworkInfo(self):
    self.logAdapter.info("Updating network info from driver")
    return self.__readDriverNetworkInfo().bind(self.saveDriverNetworkInfo)

  def postLaunch(self):
    return self.setHostname() \
      .then(self.mountFolders) \
      .then(self.uploadKeys)
 
  def saveDriverNetworkInfo(self, info):
    self.logAdapter.debug("Network information for machine: %s" % info)
    net = self.config.get('network', OrderedDict())
    net.update(info) 
    self.config.set('network', net)
    return self.config.saveConfig()

  def start(self):

    state = self.fetchState()
    if state.isFail():
      return state

    if state.getOK() is EngineStates.RUNNING:
      return EngineAlreadyRunning("Engine \"%s\" is already running" % self.name)

    if state.getOK() is EngineStates.SUSPENDED:
      return self.__start().then(self.__waitForReady) 
    else:
      return self.__configure() \
        .then(self.updateNetworkInfo) \
        .then(self.__start) \
        .then(self.__waitForReady) \
        .then(self.__waitForNetwork) \
        .then(self.postLaunch) 

  def readBox(self):
    return self.core.readBox(self.config.get('box'))
    
  def provision(self):

    logger.info("Provisioning engine \"%s\" with driver \"%s\"", self.name, self.config.get('driver'))

    prov = self.validateProvision()
    if prov.isFail():
      return prov
    elif prov.getOK():
      return OK(self)

    box = self.readBox().bind(Box.fetch)
    if box.isFail():
      return box
    box = box.getOK()
 
    return self.getDriver().importMachine(self.name, box.getOVFFile(), self.getEngineProfile()) \
      .bind(self.setDriverID) \
      .then(self.config.saveConfig) \
      .map(self.chainSelf)
      #.then(self.__configure) \
      #.then(self.updateNetworkInfo) \

  def deprovision(self):

    if not self.isProvisioned():  
      return Fail(EngineNotProvisioned("Engine \"%s\" is not provisioned." % self.name, self))

    self.__cacheLink(None)

    return self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfTrue(self.__terminate) \
      .then(self.__delete) \
      .then(self.clearDriverID)  \
      .then(self.config.saveConfig)  \
      .then(self.removeFromHostsFile) \
      .then(dinfo("Engine \"%s\" has been deprovisioned.", self.name)) \
      .map(self.chainSelf)

  def suspend(self):
    if not self.isProvisioned():
      return Fail(EngineNotProvisioned("Engine \"%s\" is not provisioned." % self.name))   
    self.__cacheLink(None)

    return self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfFalse(failWith(EngineNotRunning("Engine \"%s\" is not running." % self.name))) \
      .then(self.__suspend) \
      .then(dinfo("Engine \"%s\" has been suspended.", self.name)) \
      .map(chainSelf)

    #XXX Insert wait for suspension

  def stop(self, force=False):

    self.__cacheLink(None)

    operation = self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfFalse(failWith(EngineNotRunning("Engine \"%s\" is not running." % self.name))) 

    if(force):
      operation >> self.__terminate >> dinfo("Engine \"%s\" has been terminated.", self.name)
    else:
      operation >> self.__halt >> dinfo("Engine \"%s\" has been halted.", self.name)

    # XXX insert wait for stopped state
    return operation.map(self.chainSelf)
     
  def readLink(self):
    if self.link is not None:
      return OK(self.link)
    link = self.core.getLink()
    return link.connectEngine(self).map(self.__cacheLink)

  def __cacheCurrentEnv(self, lr):
    env = lr.stdout.strip()
    self.logAdapter.debug("Current environment: '%s'" % (env))
    self.currentEnv = env
    return lr

  def __cacheLink(self, link):
    self.link = link
    return link

  def __start(self, *args):
    return self.getDriver().startMachine(self.getDriverID()).map(self.chainSelf)

  def __suspend(self, *args):
    return self.getDriver().suspendMachine(self.getDriverID()).map(self.chainSelf)

  def __terminate(self, *args):
    return self.getDriver().terminateMachine(self.getDriverID()).map(self.chainSelf)

  def __halt(self, *args):
    return self.getDriver().haltMachine(self.getDriverID()).map(self.chainSelf)

  def __delete(self, *args):
    return self.getDriver().deleteMachine(self.getDriverID()).map(self.chainSelf)

  def __readDriverNetworkInfo(self):
    return self.getDriver().readMachineNetworkInfo(self.getDriverID())

  def __configure(self):
    return self.getDriver().configureMachine(self.getDriverID(), self)

  def shell(self):
    return self.readLink() >> Link.interactive

  def __waitForNetwork(self):
    self.logAdapter.info("Waiting for machine network...")
    return self.getDriver().readMachineWaitForNetwork(self.getDriverID())

  def __waitForReady(self):
    self.logAdapter.info("Waiting for machine to boot...")
    return self.readLink()

  def setHostname(self):
    self.logAdapter.info("Configuring machine hostname")
    dns = self.getDNSName()
    echoCmd = "echo %s > /etc/hostname" % dns
    hostCmd = "hostname %s" % dns 
    hostsCmd = "sed -i \"s/127.0.1.1.*/127.0.1.1\t%s/g\" /etc/hosts" % self.name
    #hostsCmd = "hostnamectl set-hostname %s" % dns
    serviceCmd = "service hostname restart"
    cmd = "sudo -- bash -c '%s && %s && %s && %s'" % (echoCmd, hostsCmd, hostCmd, serviceCmd)
    cmds = list(map(defer(self.link.runCommand, stream=True, sudo=False), [cmd]))
    return Try.sequence(cmds) 

  def uploadKeys(self):
    ''' pass '''
    ops = []
    key = self.core.getSSHPrivateKey()
    pkey = self.core.getSSHPublicKey()

    if key.isOK():
      key = key.getOK()
      self.logAdapter.info("Uploading private key: %s" % key)
      ops.append( self.readLink().bind(Link.upload, localPath=key, remotePath=".ssh/id_dsa") )
  
    if pkey.isOK():
      pkey = pkey.getOK()
      self.logAdapter.info("Uploading public key: %s" % pkey)
      ops.append( self.readLink().bind(Link.upload, localPath=pkey, remotePath=".ssh/id_dsa.pub") )
      ops.append( self.readLink().bind(Link.runCommand, cmd="t=$(tempfile); cat ~/.ssh/authorized_keys ~/.ssh/id_dsa.pub | sort -u > $t && mv $t ~/.ssh/authorized_keys", stream=True, interactive=True) )

    return Try.sequence(ops)
  
  def exposePort(self, local_port, public_port, scheme):
    keyfile = self.core.getSSHPrivateKey()
    if keyfile.isFail():
      return keyfile
    keyfile = Shell.normalizePath(keyfile.getOK())
    forward_descr = "0.0.0.0:%s:127.0.0.1:%s" % (public_port, local_port)
    engineIP = self.getSSHIP()
    enginePort = str(self.getSSHPort())
    cmdPath = "ssh"
    cmdArgs = ["ssh", "-N", "-L", forward_descr, engineIP, "-l", "substance", "-p", enginePort, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-i", keyfile]
    sudo = False
    if public_port < 1024 and not Shell.isCygwin():
      sudo = True
    self.logAdapter.info("Exposing port %s as %s; kill the process (CTRL-C) to un-expose.", local_port, public_port)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
      s.connect(("8.8.8.8", 80))
      ip = s.getsockname()[0]
      if scheme:
        self.logAdapter.info("%s://%s:%s is now available.", scheme, ip, public_port)
      else:
        self.logAdapter.info("Others can now connect to port %s via IP %s.", public_port, ip)
    Shell.execvp(cmdPath, cmdArgs, {}, sudo=sudo)
 
  def envSwitch(self, subenvName, restart=False):
    self.logAdapter.info("Switch engine '%s' to subenv '%s'" % (self.name, subenvName))
    cmds = [
      "subenv init '/substance/devroot/%s'" % (subenvName),
      "subenv use '%s'" % (subenvName),
    ]

    if restart:
      cmds.append("dockwrkr -y reset")
      cmds.append("subenv run dockwrkr pull -a")
      cmds.append("subenv run dockwrkr start -a")

    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, sudo=False) \
      .then(self.envRegister)


  def envRegister(self):
    return self.readLink() \
      .bind(Link.runCommand, 'subenv vars', stream=False, capture=True) \
      .bind(self.__envRegister)

  def __envRegister(self, lr):
    vars = lr.stdout.split("\n")
    env =  Try.attempt(parseDotEnv, vars)
    if env.isFail():
      return env
    env = env.getOK()
    if 'SUBENV_FQDN' in env:
      return SubHosts.register(env['SUBENV_FQDN'], self.getPublicIP())
    elif 'SUBENV_NAME' in env: 
      return SubHosts.register(env['SUBENV_NAME'] + self.core.config.get('tld'), self.getPublicIP())
       
  def envLoadCurrent(self):
    cmds = [ "subenv current" ]
    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=False, sudo=False, capture=True) \
      .map(self.__cacheCurrentEnv) \
      .catch(lambda err: Fail(EnvNotDefinedError("No current subenv is set. Check 'switch' for detais."))) \
      .then(lambda: self)

 
  def envStart(self, reset=False, containers=[]):
    cmds = []
    if reset:
      cmds.append("dockwrkr -y reset")

    if len(containers) > 0:
      self.logAdapter.info("Starting %s container(s)" % (' '.join(containers)))
      cmds.append('subenv run dockwrkr start %s' % ' '.join(containers))
    else:
      self.logAdapter.info("Starting all containers...")
      cmds.append('subenv run dockwrkr start -a')

    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, sudo=False) 

  def envRestart(self, time=10, containers=[]):
    cmds = []

    if len(containers) > 0:
      self.logAdapter.info("Restarting %s containers" % (' '.join(containers)))
      cmds.append('subenv run dockwrkr restart -t %s %s' % (time, ' '.join(containers)))
    else:
      self.logAdapter.info("Restarting all containers...")
      cmds.append('subenv run dockwrkr restart -a -t %s' % time)

    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, sudo=False) 

  def envRecreate(self, time=10, containers=[]):
    cmds = []

    if len(containers) > 0:
      self.logAdapter.info("Recreating %s containers" % (' '.join(containers)))
      cmds.append('subenv run dockwrkr recreate -t %s %s' % (time, ' '.join(containers)))
    else:
      self.logAdapter.info("Recreating all containers...")
      cmds.append('subenv run dockwrkr recreate -a -t %s' % time)

    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, sudo=False) 

  def envShell(self, container=None, user=None, cwd=None):
    if container:
      return self.envEnter(container, user, cwd)
    else:
      return self.readLink().bind(Link.interactive)
   
  def envEnter(self, container, user=None, cwd=None):
    self.logAdapter.info("Entering %s container..." % (container))
    return self.envExec(container, ["exec /bin/bash"] , cwd, user)

  def envExec(self, container, cmd, cwd=None, user=None):
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

    cmd = "subenv run dockwrkr exec -t -i %(opts)s %(container)s 'bash -c \"%(initCommands)s\"'" % tpl
    return self.readLink().bind(Link.runCommand, cmd=cmd, interactive=True, stream=True, shell=False, capture=False)

  def envExecAlias(self, alias, args):
    aliases = self.config.get('aliases')
    if aliases and alias in aliases:
      cmd = aliases[alias]
      args = cmd['args'] + args
      return self.envExec(container=cmd['container'], cmd=args, cwd=cmd['cwd'], user=cmd['user'])
    return Fail("Invalid command '%s' specified for '%s'.\n\nUse 'substance help' for available commands." % (alias, 'substance'))

  def envStop(self, time=10, containers=[]):
    cmds = []
    if len(containers) > 0:
      self.logAdapter.info("Stopping %s container(s)" % (' '.join(containers)))
      cmds.append('subenv run dockwrkr stop -t %s %s' % (time, ' '.join(containers)))
    else:
      self.logAdapter.info("Stopping containers...") 
      cmds.append('subenv run dockwrkr stop -a -t %s' % time)

    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, sudo=False) 

  def envStatus(self, full=False):
    if full:
      cmds = []
      cmds.append('subenv run dockwrkr status')
      return self.readLink() \
        .bind(Link.runCommand, ' && '.join(cmds), stream=False, sudo=False, capture=True) \
        .map(self.__envStatus)
    else:
      return OK(self.__envStatus())

  def envLogs(self, parts=[], pattern=None, follow=True, lines=None):

    if not pattern:
      pattern = "%s*.log" % ('-'.join(parts))
     
    cmds = []
    cmd = "tail"
    if follow:
      cmd += " -f"
    if lines:
      cmd += " -n %s" % int(lines)

    cmd += " \"logs/%s\"" % pattern 

    cmds.append('subenv run %s' % cmd)
    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, capture=False, sudo=False) 

  def envListLogs(self, parts=[], pattern=None):

    if not pattern:
      pattern = "%s*.log" % ('-'.join(parts))
     
    cmds = []
    cmd = "ls -1 \"logs/%s\" | xargs -n1 basename" % pattern

    cmds.append('subenv run %s' % cmd)
    return self.readLink() \
      .bind(Link.runCommand, ' && '.join(cmds), stream=True, capture=False, sudo=False) 
  
  def __envStatus(self, containers=None):
    return {
      'engine': self,
      'containers': containers.stdout + containers.stderr if containers else None
    }
     
  def envDocker(self, command):
    cmd = "docker %s" % command
    logger.debug("DOCKER: %s" % cmd)
    return self.readLink().bind(Link.runCommand, cmd, stream=True, interactive=True, shell=False)

      
  def getEngineFolders(self):
    #XXX Dynamic mounts / remove hardcoded values.
    devroot = self.config.get('devroot')
    pfolder = EngineFolder(
      name='devroot', 
      mode=devroot.get('mode'),
      hostPath=os.path.expanduser(devroot.get('path')),
      guestPath='/substance/devroot',
      uid=1000,
      gid=1000,
      umask="0022",
      excludes=devroot.get('excludes', []),
      syncArgs=devroot.get('syncArgs', [])
    )
    return [pfolder]
 
  def mountFolders(self):
    self.logAdapter.info("Mounting engine folders")
    folders = self.getEngineFolders()
    return Try.of(list(map(self.mountFolder, folders)))
 
  def mountFolder(self, folder):
    mountCmd = "mount -t vboxsf -o umask=%(umask)s,gid=%(gid)s,uid=%(uid)s %(name)s %(guestPath)s" % folder.__dict__
    mkdirCmd = "mkdir -p %(guestPath)s && chown -R %(uid)s:%(gid)s %(guestPath)s" % folder.__dict__
    # XXX Make this non VBOX specific
    return self.link.runCommand(mkdirCmd, sudo=True) \
      .then(defer(self.link.runCommand, mountCmd, sudo=True))
    
  chainSelf = chainSelf

  def __repr__(self):
    return "Engine(%s)" % self.name
