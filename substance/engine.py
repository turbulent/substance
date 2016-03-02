# -*- coding: utf-8 -*-
# $Id$

import sys
import os
import logging
import yaml
from substance.driver.virtualbox import VirtualBoxDriver
from substance.constants import ( EngineStates )
from substance.exceptions import ( 
  FileSystemError, 
  ConfigSyntaxError, 
  EngineNotProvisioned ,
  EngineAlreadyRunning
)

class EngineProfile:
  cpus = None
  memory = None

  def __init__(self, cpus=2, memory=1024):
    self.cpus = cpus
    self.memory = memory

class Engine:

  config = None
  profile = None
  defaultConfig = {
    "name": "default", 
    "driver": "VirtualBox",
    "id": None,
    "profile": { "memory": 1024, "cpus": 2 },
    "docker": { "port": 2375, "tls": False, "certificateFile": None },
    "network": { "privateIP": None, "publicIP": None, "sshIP": None, "sshPort": None },
    "projectsPath": "~/dev/projects",
    "mounts": ['a','b','c']
  }

  def __init__(self, name, enginePath=None):
    self.name = name 
    self.enginePath = enginePath
    self.configFile = os.path.join( self.enginePath, "engine.yml" )

  def getName(self):
    return self.name

  def getID(self):
    return self.config.id

  def getEnginePath(self):
    return self.enginePath

  def getEngineFilePath(self, fileName):
    return os.path.join( self.enginePath, fileName)

  def getDockerURL(self):
    return "tcp://%s:%s" % (self.config.get('ip', 'INVALID'), self.config.get('docker_port', 2375))
 
  def readConfig(self):
    if os.path.isfile(self.configFile):
      try:
        stream = open(self.configFile, "r")
        self.config = yaml.load(stream)
      except yaml.YAMLError, exc:
        msg = "Syntax error in file %s"
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            msg += " Error position: (%s:%s)" % (mark.line+1, mark.column+1)
        raise ConfigSyntaxError(msg)
      except Exception as err:
        raise FileSystemError("Failed to read engine configuration file %s : %s" % (self.configFile, err))
    else:
      logging.info("Generating default substance configuration in %s" % self.configFile)
      self.defaultConfig["name"] = self.name
      self.saveConfig( self.defaultConfig )
    return self.config

  def generateDefaultConfig(self, config=None, profile=None):
    logging.info("Generating default substance configuration in %s" % self.configFile)

    if config:
      for k, v in config.iteritems():
        self.defaultConfig.set(key, v)
    if profile:
      self.defaultConfig.get('profile')['memory'] = profile.memory
      self.defaultConfig.get('profile')['cpus'] = profile.cpus
    self.defaultConfig["name"] = self.name

    self.saveConfig( self.defaultConfig )

  def saveConfig(self, config=None):
    config = config if config  else self.config
    try:
      logging.debug("saveConfig: %s" % (config))
      with open(self.configFile, "w") as fileh:
        fileh.write(yaml.dump( config, default_flow_style=False))
    except Exception as err:
      raise FileSystemError("Failed to write configuration to %s: %s" % (self.configFile, err))

  def getDriver(self):
    return {
      'VirtualBox': VirtualBoxDriver()
    }.get(self.config.get('driver', 'VirtualBox'))

  def getEngineProfile(self):
    profile = self.config.get('profile', {})
    return EngineProfile(**profile)

  def getDriverID(self):
    return self.config.get('id', None)

  def isProvisioned(self):
    '''
    Check that this engine has an attached provisioned Virtual Machine.
    '''
    machineID = self.getDriverID()
    if not machineID:
      return False
  
    if self.getDriver().exists(machineID):
      return True

  def isRunning(self):
    if not self.isProvisioned():
      return False

    state = self.getDriver().getMachineState(self.getDriverID())
    return True if state is EngineStates.RUNNING else False
    
 
  def launch(self):

    # 1. Check that we know about a provisioned machined for this engine. Provision if not.
    # 2. Validate that the machine we know about is still provisioned. Provision if not.
    # 3. Check the machine state, boot accordingly
    # 4. Setup guest networking
    # 4. Fetch the guest IP from the machine and store it in the machine state.

    if not self.isProvisioned():
      self.provision()

    self.start()
 
  def start(self):
    if self.isRunning():
      raise EngineAlreadyRunning("Engine \"%s\" is already running" % self.name)

    logging.info("Booting engine VM")  
    self.getDriver().startMachine(self.getDriverID())

    # XXX insert wait for verification

  def provision(self):
    logging.info("Provisioning engine \"%s\" with driver \"%s\"" % (self.name, self.config['driver']))

    machineID = self.getDriver().importMachine(self.name, "/Users/bbeausej/dev/substance-engine/box.ovf", self.getEngineProfile())
    self.config['id'] = machineID
    self.saveConfig()
 
  def deprovision(self):
    driver = self.getDriver()
    machID = self.getDriverID()

    if not machID:
      raise EngineNotProvisioned("Engine \"%s\" is currently not provisioned.")

    if self.isRunning():
      driver.terminateMachine(machID)

    return driver.deleteMachine(machID)

  def stop(self, force=False):
    if self.isRunning():
      driver = self.getDriver()
      if force:
        driver.terminateMachine(self.getDriverID())
      else:
        driver.haltMachine(self.getDriverID())

    # XXX insert wait for verification
