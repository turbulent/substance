import sys
import os
import logging
import yaml
from substance.shell import Shell
from substance.engine import Engine

class Core:

  config = None
  defaultConfig = { "default": True }

  def __init__(self, configFile=None, basePath=None, assumeYes=False):
    self.basePath = os.path.abspath(basePath) if basePath else os.path.expanduser('~/.substance')
    self.enginesPath = os.path.join(self.basePath, "engines")

    self.configFile = configFile if configFile else "substance.yml"
    self.configFile = os.path.join(self.basePath, self.configFile)

  def assertPaths(self):
    self.makeDirectory(self.basePath)
    self.makeDirectory(self.enginesPath)

  def makeDirectory(self, path, mode=0750):
    if not os.path.exists( path ) :
      try:
        os.makedirs( path, mode )
      except Exception as err:
        raise Exception("Failed to create %s: %s" % (path,err))

  def getBasePath(self):
    return self.basePath

  def getEnginesPath(self):
    return self.enginesPath
 
  def getConfigFile(self):
    return self.configFile

  def getConfig(self):
    if not self.config:
      self.readConfig()
    return self.config

  def saveConfig(self, config=None):
    config = config or self.config 
    try:
      with open(self.configFile, "w") as fileh:
        fileh.write(yaml.dump( config, default_flow_style=False))
    except Exception as err:
      raise Exception("Failed to write configuration to %s : %s" % (self.configFile, err)) 

  def readConfig(self):
    if os.path.isfile( self.configFile ):
      try:
        stream = open(self.configFile, "r")
        self.config = yaml.load(stream)
      except Exception as err:
        raise Exception("Failed to read configuration file %s : %s" % (self.configFile, err)) 
    else:
      logging.info("Generating default substance configuration in %s" % self.configFile)
      self.saveConfig( self.defaultConfig )
    return self.config

  def getEngines(self):
    self.assertPaths()
    dirs = [d for d in os.listdir(self.enginesPath) if os.path.isdir(os.path.join(self.enginesPath, d))]
    return dirs

  def getEngine(self, name):
    self.assertPaths()
    enginePath = os.path.join(self.enginesPath, name)
    if not os.path.isdir(enginePath):
      raise Exception("Engine %s does not exist." % name)

    return Engine(name, enginePath)
     
