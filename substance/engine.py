import os
import logging
from collections import (OrderedDict, namedtuple)
import substance.core
from substance.monads import *
from substance.config import (Config)
from substance.logs import *
from substance.shell import Shell
from substance.link import Link
from substance.box import Box
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
)

class EngineProfile(object):
  def __init__(self, cpus=2, memory=1024):
    self.cpus = cpus
    self.memory = memory

  def __repr__(self):
    return "%s" % {'cpus': self.cpus, 'memory': self.memory}


class EngineFolder(object):
  def __init__(self, name, hostPath, guestPath, uid=None, gid=None, umask=None):
    self.name = name
    self.hostPath = hostPath
    self.guestPath = guestPath
    self.uid = uid if uid else 1000
    self.gid = gid if gid else 1000
    self.umask = umask if umask else "0022"

  def __repr__(self):
    return "EngineFolder(name=%(name)s, host:%(hostPath)s -> guest:%(guestPath)s)" % self.__dict__


class Engine(object):

  def __init__(self, name, enginePath, core):
    self.name = name
    self.enginePath = enginePath
    self.core = core
    self.link = core.getLink()
    configFile = os.path.join(self.enginePath, "engine.yml")
    self.config = Config(configFile)

  def getDefaults(self):
    defaults = OrderedDict()
    defaults['name'] = 'default'
    defaults['driver'] = 'virtualbox'
    defaults['id'] = None
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
    defaults['projectsPath'] = '~/dev/projects'
    defaults['mounts'] = []
    return defaults
  
  def validateConfig(self, config):
    fields = ['name','driver','profile','docker','network','projectsPath','mounts', 'box']

    self.config.validateFieldsPresent(config.getConfig(), fields)

    if config.get('name', None) != self.name:
      return Fail(ConfigValidationError("Invalid name property in configuration (got %s expected %s)" %(config.get('name'), self.name)))

    driver = config.get('driver', None)
    if not self.core.validateDriver(driver):
      return Fail(ConfigValidationError("Invalid driver property in configuration (%s is not supported)" % driver))

    return OK(config.getConfig())

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
      .bind(self.validateConfig) \
      .then(self.config.saveConfig) \
      .bind(dinfo("Generated default engine configuration in %s", self.config.configFile)) \
      .map(self.chainSelf)
 
  def remove(self):
    if not os.path.isdir(self.enginePath):
      return Fail(FileSystemError("Engine \"%s\" does not exist." % self.name))
    if self.isProvisioned():
      return Fail(EngineProvisioned("Engine \"%s\" is provisioned." % self.name))
    return Shell.nukeDirectory(self.enginePath)
 
  def makeDefaultConfig(self, config=None, profile=None):
    default = self.getDefaults()
    default["name"] = self.name

    for ck, cv in default.iteritems():
      self.config.set(ck, cv)

    if config:
      for kkk, vvv in config.iteritems():
        self.config.set(kkk, vvv)

    if profile:
      self.config.get('profile')['cpus'] = profile.cpus
      self.config.get('profile')['memory'] = profile.memory

    return OK(self.config)

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


  def updateNetworkInfo(self):
    logging.info("Updating network info from driver")
    return self.__readDriverNetworkInfo().bind(self.saveDriverNetworkInfo)

  def postLaunch(self):
    return self.setHostname() \
      .then(self.mountFolders)
 
  def saveDriverNetworkInfo(self, info):
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
        .then(self.postLaunch)

  def readBox(self):
    return self.core.readBox(self.config.get('box'))
    
  def provision(self):

    logging.info("Provisioning engine \"%s\" with driver \"%s\"", self.name, self.config.get('driver'))

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

    return self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfTrue(self.__terminate) \
      .then(self.__delete) \
      .then(self.clearDriverID)  \
      .then(self.config.saveConfig)  \
      .then(dinfo("Engine \"%s\" has been deprovisioned.", self.name)) \
      .map(self.chainSelf)

  def suspend(self):
    if not self.isProvisioned():
      return Fail(EngineNotProvisioned("Engine \"%s\" is not provisioned." % self.name))   
       
    return self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfFalse(failWith(EngineNotRunning("Engine \"%s\" is not running." % self.name))) \
      .then(self.__suspend) \
      .then(dinfo("Engine \"%s\" has been suspended.", self.name)) \
      .map(chainSelf)

    #XXX Insert wait for suspension

  def stop(self, force=False):
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
    if not self.link:
      self.link = self.core.getLink()
    return self.link.connectEngine(self)

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

  def __waitForReady(self):
    logging.info("Waiting for machine to boot...")
    return self.readLink()

  def setHostname(self):
    logging.info("Configuring machine hostname")
    hostCmd = "hostname %s" % self.name
    hostsCmd = "sed -i 's/substance-min/%s/g' /etc/hosts" % self.name
    serviceCmd = "service hostname restart"
    echoCmd = "echo %s > /etc/hostname" % self.name
    cmd = "sudo -- bash -c '%s && %s && %s && %s'" % (echoCmd, hostCmd, hostsCmd, serviceCmd)
    cmds = map(defer(self.link.runCommand, stream=True, sudo=False), [cmd])
    return Try.sequence(cmds) 
 
  def getEngineFolders(self):
    pfolder = EngineFolder(
      name='projects',
      hostPath=os.path.expanduser(self.config.get('projectsPath')),
      guestPath='/projects',
      uid=1000,
      gid=1000,
      umask="0022"
    )
    return [pfolder]
 
  def mountFolders(self):
    logging.info("Mounting engine folders")
    folders = self.getEngineFolders()
    return Try.of(map(self.mountFolder, folders))
 
  def mountFolder(self, folder):
    mountCmd = "mount -t vboxsf -o umask=%(umask)s,gid=%(gid)s,uid=%(uid)s %(name)s %(guestPath)s" % folder.__dict__
    mkdirCmd = "mkdir -p %(guestPath)s && chown -R %(uid)s:%(gid)s %(guestPath)s" % folder.__dict__
    # XXX Make this non VBOX specific
    return self.link.runCommand(mkdirCmd, sudo=True) \
      .then(defer(self.link.runCommand, mountCmd, sudo=True))
    
  chainSelf = chainSelf

  def __repr__(self):
    return "Engine(%s)" % self.name
