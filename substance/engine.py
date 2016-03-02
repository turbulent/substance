# -*- coding: utf-8 -*-
# $Id$

import sys
import os
import logging
import yaml
from substance.exceptions import ( FileSystemError, ConfigSyntaxError )
from substance.driver.virtualbox import VirtualBoxDriver

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
    config = config or self.config
    try:
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

  def launch(self):
    driver = self.getDriver()

    driver.importMachine(self.name, "/Users/bbeausej/dev/substance-engine/box.ovf", self.getEngineProfile())
    driver.startMachine(self.name)
 
  def deprovision(self):
    driver = self.getDriver()
    driver.destroyMachine(self.config.id)  
