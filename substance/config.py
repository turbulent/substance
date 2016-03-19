import os
import logging
from substance.monads import *
from substance.shell import Shell
from substance.utils import (readYAML,writeYAML)
from substance.exceptions import (FileSystemError)


class Config(object):

  loaded = False
  config = {}

  def __init__(self, configFile=None):
    self.configFile = configFile

  def getConfigFile(self):
    return OK(self.configFile)

  def set(self, key, value):
    self.config[key] = value
    return value

  def get(self, key, default=None):
    return self.config.get(key, None)

  def getConfig(self):
    return self.config

  def setConfig(self, config):
    self.config = config
    return OK(self.config)

  def saveConfig(self):
    return Try.attempt(writeYAML, self.configFile, self.config)

  def readConfigFile(self):
    return Try.attempt(readYAML, self.configFile)

  def loadConfigFile(self):
    if not os.path.exists(self.configFile):
      return Fail(FileDoesNotExist("File does not exist: %s" % self.configFile))
    return self.readConfigFile() >> self.setConfig

  def generateDefaultConfigFile(self):
    logging.info("Generating default substance configuration in %s", self.configFile)

    if config:
      for kkk, vvv in config.iteritems():
        self.defaultConfig.set(kkk, vvv)
    if profile:
      self.defaultConfig.get('profile')['memory'] = profile.memory
      self.defaultConfig.get('profile')['cpus'] = profile.cpus
    self.defaultConfig["name"] = self.name

    self.saveConfig(self.defaultConfig)

 
