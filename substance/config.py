import os
import logging
from substance.monads import *
from substance.shell import Shell
from substance.utils import (readYAML, writeYAML)
from substance.exceptions import (FileSystemError, FileDoesNotExist)

from collections import namedtuple


class Config(object):

  loaded = False
  config = {}

  def __init__(self, configFile=None):
    self.configFile = configFile

  def getConfigFile(self):
    return self.configFile

  def set(self, key, value):
    self.config[key] = value
    return value

  def get(self, key, default=None):
    return self.config.get(key, default)

  def getBlockKey(self, block, key, default=None):
    return self.config.get(block, {}).get(key, default)

  def getConfig(self):
    return self.config

  def setConfig(self, config):
    self.config = config
    return OK(self)

  def saveConfig(self, config=None):
    config = self.config if not config else config
    return Try.attempt(writeYAML, self.configFile, config)

  def readConfigFile(self):
    return Try.attempt(readYAML, self.configFile)

  def loadConfigFile(self):
    if not os.path.exists(self.configFile):
      return Fail(FileDoesNotExist("File does not exist: %s" % self.configFile))
    logging.debug("Loading config file: %s", self.configFile)
    return self.readConfigFile() >> self.setConfig
  
  def validateFieldsPresent(self, block, fields):
    reducer = lambda acc,x: Fail("Property does not exist in configuration: %s" % x) if not x in block else OK(None)
    return reduce(reducer, fields, OK(None))

