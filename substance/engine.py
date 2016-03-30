import os
import logging
from collections import OrderedDict
import substance.core
from substance.monads import *
from substance.config import (Config)
from substance.logs import *
from substance.shell import Shell
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
  cpus = None
  memory = None
  def __init__(self, cpus=2, memory=1024):
    self.cpus = cpus
    self.memory = memory

  def __repr__(self):
    return "%s" % {'cpus': self.cpus, 'memory': self.memory}

class Engine(object):

  def __init__(self, name, enginePath, core):
    self.name = name
    self.enginePath = enginePath
    self.core = core
    configFile = os.path.join(self.enginePath, "engine.yml")
    self.config = Config(configFile)

  def getDefaultConfig(self):
    defaults = OrderedDict()
    defaults['name'] = 'default'
    defaults['driver'] = 'VirtualBox'
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
    defaults['network']['sshPort'] = None
    defaults['projectsPath'] = '~/dev/projects'
    defaults['mounts'] = []
    return defaults

  def validateConfig(self):
    if self.config.get('name', None) != self.name:
      return Fail(ConfigValidationError("Invalid name property in configuration (got %s expected %s)" %(self.config.get('name'), self.name)))

    driver = self.config.get('driver', None)
    if not self.core.validDriver(driver):
      return Fail(ConfigValidationError("Invalid driver property in configuration (%s is not supported)" % driver))

    return OK(self.config.getConfig())

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
      return "tcp://%s:%s" % (self.config.get('ip', 'INVALID'), self.config.get('docker_port', 2375))

  def getDriver(self):
    return {
      'VirtualBox': VirtualBoxDriver()
    }.get(self.config.get('driver', 'VirtualBox'))

  def getEngineProfile(self):
    profile = self.config.get('profile', {})
    return EngineProfile(**profile)

  def getDriverID(self):
    return self.config.get('id', None)

  def setDriverID(self, driverID):
    self.config.set('id', driverID)
    return OK(self)

  def clearDriverID(self):
    self.config.set('id', None)
    return OK(self)

  def loadConfigFile(self):
    return self.config.loadConfigFile().then(self.validateConfig).map(self.chainSelf)

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
      .bind(self.config.saveConfig) \
      .bind(dinfo("Generated default substance configuration in %s", self.config.configFile)) \
      .map(self.chainSelf)
 
  def remove(self):
    if not os.path.isdir(self.enginePath):
      return Fail(FileSystemError("Engine \"%s\" does not exist." % self.name))
    if self.isProvisioned():
      return Fail(EngineProvisioned("Engine \"%s\" is provisioned." % self.name))
    return Shell.nukeDirectory(self.enginePath)
 
  def makeDefaultConfig(self, config=None, profile=None):
    default = self.getDefaultConfig()
    default["name"] = self.name

    if config:
      for kkk, vvv in config.iteritems():
        default[kkk] = vvv

    if profile:
      default.get('profile')['cpus'] = profile.cpus
      default.get('profile')['memory'] = profile.memory

    return OK(default)

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
    isRunningState = (lambda state: (state is EngineStates.RUNNING))
    return self.fetchState().map(isRunningState)

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
    return self.provision().then(self.start)

  def start(self):

    return self.validateProvision() \
      .thenIfTrue(self.isRunning) \
      .thenIfTrue(failWith(EngineAlreadyRunning("Engine \"%s\" is already running" % self.name))) \
      .then(self.__start) \

  def provision(self):

    if self.isProvisioned():
      return OK(None)

    logging.info("Provisioning engine \"%s\" with driver \"%s\"", self.name, self.config.get('driver'))

    return self.getDriver().importMachine(self.name, "/Users/bbeausej/dev/substance-engine/box.ovf", self.getEngineProfile()) \
      .bind(self.setDriverID) \
      .then(self.config.saveConfig) \
      .map(self.chainSelf)

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
 
  chainSelf = chainSelf

  def __repr__(self):
    return "Engine(%s)" % self.name
