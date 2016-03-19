import os
import logging
from substance.monads import *
from substance.config import (Config)
from substance.logs import *
from substance.shell import Shell
from substance.driver.virtualbox import VirtualBoxDriver
from substance.constants import (EngineStates)
from substance.exceptions import (FileSystemError, EngineAlreadyRunning, EngineExistsError)

class EngineProfile(object):
  cpus = None
  memory = None
  def __init__(self, cpus=2, memory=1024):
    self.cpus = cpus
    self.memory = memory

  def __repr__(self):
    return "%s" % {'cpus': self.cpus, 'memory': self.memory}

class Engine(object):

  config = None
  profile = None
  defaultConfig = {
    "name": "default",
    "driver": "VirtualBox",
    "id": None,
    "profile": {"memory": 1024, "cpus": 2},
    "docker": {"port": 2375, "tls": False, "certificateFile": None},
    "network": {"privateIP": None, "publicIP": None, "sshIP": None, "sshPort": None},
    "projectsPath": "~/dev/projects",
    "mounts": ['a', 'b', 'c']
  }

  def __init__(self, name, enginePath=None):
    self.name = name
    self.enginePath = enginePath
    configFile = os.path.join(self.enginePath, "engine.yml")
    self.config = Config(configFile)

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

  def loadConfigFile(self):
    return self.config.loadConfigFile().map(self.chainSelf)

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
      .bind(self.config.saveConfig) 
      #.bind(info("Generated default substance configuration in %s", self.config.configFile)) 
 
  def remove(self):
    if not os.path.isdir(self.enginePath):
      return Fail(EngineExistsError("Engine \"%s\" does not exist." % self.name))
    return Shell.nukeDirectory(self.enginePath)
 
  def makeDefaultConfig(self, config=None, profile=None):
    logging.info("Generating default substance configuration in %s", self.config.configFile)

    default = self.defaultConfig.copy()
    default["name"] = self.name

    if config:
      for kkk, vvv in config.iteritems():
        default.set(kkk, vvv)

    if profile:
      default.get('profile')['memory'] = profile.memory
      default.get('profile')['cpus'] = profile.cpus

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
    return self.getDriver().exists(matchID)

  def isRunning(self):
    isRunningState = (lambda state: (state is EngineStates.RUNNING))
    return self.validateProvision().bindIfTrue(lambda x: self.fetchState().map(isRunningState))

    #if not self.isProvisioned():
    #  return False
    #state = self.fetchState()
    #return True if state is EngineStates.RUNNING else False

  def fetchState(self):
    if not self.isProvisioned():
      return OK(EngineStates.INEXISTENT)
    return self.getDriver().getMachineState(self.getDriverID())
   
    #if not self.isProvisioned():
    #  return Fail(EngineNotProvisioned("Engine %s is not provisioned." % self.name))
    #return self.getDriver().getMachineState(self.getDriverID())

  def launch(self):

    # 1. Check that we know about a provisioned machined for this engine. Provision if not.
    # 2. Validate that the machine we know about is still provisioned. Provision if not.
    # 3. Check the machine state, boot accordingly
    # 4. Setup guest networking
    # 4. Fetch the guest IP from the machine and store it in the machine state.

    self.provision().bind(self.start())

    #if not self.isProvisioned(validate=True):
    #  self.provision()
    #self.start()

  def start(self):

    return self.isRunning() \
      .bindIfTrue(failWith(EngineAlreadyRunning("Engine \"%s\" is already running" % self.name))) \
      .bind(self.__start)

    #if self.isRunning():
    #  raise EngineAlreadyRunning("Engine \"%s\" is already running" % self.name)
    #logging.info("Booting engine VM")
    #return self.getDriver().startMachine(self.getDriverID())


  def provision(self):

    if self.isProvisioned():
      return OK()

    dinfo("Provisioning engine \"%s\" with driver \"%s\"", self.name, self.config['driver'])()

    return self.getDriver().importMachine(self.name, "/Users/bbeausej/dev/substance-engine/box.ovf", self.getEngineProfile()) \
      .bind(Engine.setMachineID) \
      .then(self.config.saveConfig)

   # machineID = self.getDriver().importMachine(self.name, "/Users/bbeausej/dev/substance-engine/box.ovf", self.getEngineProfile())
   # self.config['id'] = machineID
   # self.saveConfig()

  def deprovision(self):

    if not self.isProvisioned():  
      return Fail(EngineNotProvisioned("Engine \"%s\" is not provisioned.", self.name))

    return self.isRunning() \
      .bindIfTrue(self.__terminate) \
      .bind(self.__delete) \
      .bind(self.clearProvision)  \
      .then(info("Engine \"%s\" has been deprovisioned.", self.name))

  def clearProvision(self):
    self.config.set('id', None)
    return self.saveConfig() 

  def suspend(self):
    if not self.isProvisioned():
      return Fail(EngineNotProvisioned("Engine \"%s\" is not provisioned." % self.name))   
       
    return self.isRunning() \
      .bindIfFalse(failWith(EngineNotRunning("Engine \"%s\" is not running." % self.name))) \
      .bind(self.__suspend) 

    #XXX Insert wait for suspension

#    if not self.isProvisioned():
#      logging.warning("Engine \"%s\" is not provisioned.", self.name)
#      return
#
#    if not self.isRunning():
#      logging.warning("Engine \"%s\" is not running.", self.name)
#      return
#
#    self.getDriver().suspendMachine(self.getDriverID())
#    logging.info("Engine \"%s\" has been suspended.", self.name)


  def stop(self, force=False):
    operation = self.isRunning() \
      .bindIfFalse(failWith(EngineNotRunning("Engine \"%s\" is not running." % self.name))) 

    if(force):
      operation >> self.__terminate >> dinfo("Engine \"%s\" has been terminated.", self.name)
    else:
      operation >> self.__halt >> dinfo("Engine \"%s\" has been halted.", self.name)

    # XXX insert wait for stopped state
    return operation
     
#    if self.isRunning():
#      driver = self.getDriver()
#      if force:
#        driver.terminateMachine(self.getDriverID())
#        logging.info("Engine \"%s\" has been terminated.", self.name)
#      else:
#        driver.haltMachine(self.getDriverID())
#        logging.info("Engine \"%s\" has been stopped.", self.name)
#      # XXX insert wait for stopped state
#    else:
#      logging.warning("Engine \"%s\" is not running.", self.name)

  def __start(self, *args):
    return self.getDriver().startMachine(self.getDriverID())

  def __suspend(self, *args):
    return self.getDriver().suspendMachine(self.getDriverID())

  def __terminate(self, *args):
    return self.getDriver().terminateMachine(self.getDriverID())

  def __halt(self, *args):
    return self.getDriver().haltMachine(self.getDriverID())

  def __delete(self, *args):
    return self.getDriver().deleteMachine(self.getDriverID())
 
  chainSelf = chainSelf

  def __repr__(self):
    return "Engine(%s)" % self.name
