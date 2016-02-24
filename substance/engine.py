import sys
import os
import logging
import yaml

class Engine:

  config = None
  defaultConfig = {"name": None, "default": True}

  def __init__(self, name, enginePath=None):
    self.name = name 
    self.enginePath = enginePath
    self.configFile = os.path.join( self.enginePath, "engine.yml" )

  def getName(self):
    return self.name

  def getDockerURL(self):
    return "tcp://%s:%s" % (self.config.get('ip', 'INVALID'), self.config.get('docker_port', 2375))
 
  def readConfig(self):
    if os.path.isfile(self.configFile):
      try:
        stream = open(self.configFile, "r")
        self.config = yaml.load(stream)
      except Exception as err:
        raise Exception("Failed to read engine configuration file %s : %s" % (self.configFile, err))
    else:
      logging.info("Generating default substance configuration in %s" % self.configFile)
      self.defaultConfig["name"] = self.name
      self.saveConfig( self.defaultConfig )
    return self.config

  def saveConfig(self, config=None):
    config = config or self.config
    try:
      with open(self.configFile, "w") as fileh:
        fileh.write(yaml.dump( config, default_flow_style=False))
    except Exception as err:
      raise Exception("Failed to write configuration to %s: %s" % (self.configFile, err))

