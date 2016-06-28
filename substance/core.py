import sys
import os
import logging
from collections import OrderedDict

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.engine import Engine
from substance.link import Link
from substance.box import Box
from substance.db import DB
from substance.constants import Tables, EngineStates
from substance.utils import (
  readYAML,
  writeYAML,
  readSupportFile,
  getSupportFile,
  streamDownload,
  makeXHRRequest,
  sha1sum
)
from substance.config import (Config)
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import (
  FileSystemError,
  FileDoesNotExist,
  EngineNotFoundError,
  EngineExistsError,
  EngineNotRunning
)
import requests

logger = logging.getLogger(__name__)

class Core(object):

  def __init__(self, configFile=None, basePath=None):
    self.basePath = os.path.abspath(basePath) if basePath else os.path.expanduser('~/.substance')
    self.enginesPath = os.path.join(self.basePath, "engines")
    self.boxesPath = os.path.join(self.basePath, "boxes")
    self.dbFile = os.path.join(self.basePath, "db.json")

    configFile = configFile if configFile else "substance.yml"
    configFile = os.path.join(self.basePath, configFile)
    self.config = Config(configFile)

    self.insecureKey = None
    self.insecurePubKey = None

    self.assumeYes = False
    self.initialized = False

  def getBasePath(self):
    return self.basePath

  def getEnginesPath(self):
    return self.enginesPath

  def getBoxesPath(self):
    return self.boxesPath

  def getDbFile(self):
    return self.dbFile

  def initialize(self):
    if self.initialized:
      return OK(None)
    return self.assertPaths().then(self.assertConfig).then(self.initializeDB).then(defer(self.setInitialized, b=True))

  def setInitialized(self, b):
    self.initialized = b

  def assertPaths(self):
    return OK([self.basePath, self.enginesPath, self.boxesPath]).mapM(Shell.makeDirectory)

  def assertConfig(self):
    return self.config.loadConfigFile()  \
      .catchError(FileDoesNotExist, self.makeDefaultConfig)

  def getDefaultConfig(self):
    defaults = OrderedDict()
    defaults['assumeYes'] = False
    defaults['drivers'] = ['virtualbox']
    defaults['tld'] = '.sub'
    defaults['devroot'] = '~/substance'
    defaults['virtualbox'] = OrderedDict()
    defaults['virtualbox']['network'] = "172.21.21.0/24"
    defaults['virtualbox']['interface'] = None
    defaults['current'] = OrderedDict()
    defaults['engine'] = None
    defaults['subenv'] = None
    return defaults
    
  def makeDefaultConfig(self, data=None):
    logger.info("Generating default substance configuration in %s", self.config.getConfigFile())
    defaults = self.getDefaultConfig()
    for kkk, vvv in defaults.iteritems():
      self.config.set(kkk, vvv)
    self.config.set("basePath", self.basePath)
    return self.config.saveConfig()

  #-- Use

  def setUse(self, engine, subenvName=None):
    ops = [ self.setCurrentEngine(engine) ]
    if subenvName:
      ops.append( engine.envSwitch(subenvName) )
    return Try.sequence(ops)

  def setCurrentEngine(self, engine):
    current = self.config.get('current')
    current.update({'engine':engine.name})
    self.config.set('current', current)
    return OK(self)

  def loadCurrentEngine(self, name=None):
    current = self.config.get('current', {}) 
    engineName = name
    if not engineName:
      engineName = current.get('engine', None)

    if not engineName:
      return Fail(EngineNotFoundError("No current engine is specified. Check the 'use' command for details."))

    engine = self.loadEngine(engineName) \
      .bind(Engine.loadConfigFile) \
      .bind(Engine.loadState) \
      .getOK()

    if engine.state is not EngineStates.RUNNING:
      return Fail(EngineNotRunning("Engine '%s' is not running." % engine.name))

    return OK(engine)

  #-- Runtime

  def setAssumeYes(self, ay):
    self.assumeYes = True
    return True

  def getAssumeYes(self):
    if self.config.get('assumeYes', False):
      return True
    elif self.assumeYes:
      return True
    return False

  def getDefaultBoxString(self):
    return self.config.get('defaultBox', 'turbulent/substance-box:0.1')

  #-- Engine library management

  def getEngines(self):
    ddebug("getEngines()")
    dirs = [ d for d in os.listdir(self.enginesPath) if os.path.isdir(os.path.join(self.enginesPath, d))] 
    return OK(dirs)

  def loadEngines(self, engines=[]):
    return OK([ self.loadEngine(x) for x in engines ] )

  def loadEngine(self, name):
    enginePath = os.path.join(self.enginesPath, name)
    if not os.path.isdir(enginePath):
      return Fail(EngineNotFoundError("Engine \"%s\" does not exist." % name))
    else:
      return OK(Engine(name, enginePath=enginePath, core=self))

  def createEngine(self, name, config=None, profile=None):
    enginePath = os.path.join(self.enginesPath, name)
    newEngine = Engine(name, enginePath=enginePath, core=self)
    return newEngine.create(config=config, profile=profile)

  def removeEngine(self, name):
    return self.loadEngine(name) \
      >> Engine.remove
 
  #-- Driver handling

  def getDrivers(self):
    return self.config.get('drivers', [])

  def validateDriver(self, driver):
    if driver in self.getDrivers():
      return OK(driver)
    return Fail(ValueError("Driver '%s' is not a valid driver."))

  def getDriver(self, name):
    cls = {
      'virtualbox': VirtualBoxDriver
    }.get(name, 'virtualbox')
    driver = cls(core=self)
    return driver

  #-- Link handling

  def getLink(self, type="ssh"):
    link = Link(keyFile=self.getInsecureKeyFile())
    return link

  #-- Database

  def getDB(self):
    return self.db

  def initializeDB(self):
    db = DB(self.dbFile)
    db = db.initialize()
    if db.isFail():
      return db
    self.db = db.getOK()
    return OK(self.db)
      
  #-- Box handling

  def readBox(self, boxstring):
    return Box.parseBoxString(boxstring) \
      .map(lambda p: Box(core=self, **p))

  #-- Keys handling

  def getInsecureKeyFile(self):
    return getSupportFile('support/substance_insecure')

  def getInsecurePubKeyFile(self):
    return getSupportFile('support/substance_insecure.pub')
 
