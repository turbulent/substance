import sys
import os
import logging
from collections import OrderedDict

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.engine import Engine
from substance.link import Link
from substance.db import DB
from substance.constants import Tables
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
  EngineExistsError
)
import requests

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

  def getBasePath(self):
    return self.basePath

  def getEnginesPath(self):
    return self.enginesPath

  def getBoxesPath(self):
    return self.boxesPath

  def getDbFile(self):
    return self.dbFile

  def initialize(self):
    return self.assertPaths().then(self.assertConfig).then(self.initializeDB)

  def assertPaths(self):
    return OK([self.basePath, self.enginesPath, self.boxesPath]).mapM(Shell.makeDirectory)

  def assertConfig(self):
    return self.config.loadConfigFile()  \
      .catchError(FileDoesNotExist, self.makeDefaultConfig)

  def getDefaultConfig(self):
    defaults = OrderedDict()
    defaults['assumeYes'] = False
    defaults['drivers'] = ['virtualbox']
    defaults['virtualbox'] = OrderedDict()
    defaults['virtualbox']['network'] = "172.21.21.0/24"
    defaults['virtualbox']['interface'] = None
    return defaults
    
  def makeDefaultConfig(self, data=None):
    logging.info("Generating default substance configuration in %s", self.config.getConfigFile())
    defaults = self.getDefaultConfig()
    for kkk, vvv in defaults.iteritems():
      self.config.set(kkk, vvv)
    self.config.set("basePath", self.basePath)
    return self.config.saveConfig()
 
  #-- Runtime

  def setAssumeYes(self, ay):
    return self.config.set('assumeYes', ay)

  def getAssumeYes(self):
    return self.config.get('assumeYes', False)

  def getDefaultBox(self):
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
    return driver in self.getDrivers()

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

  def getBoxPath(self, component=None):
    return os.path.join(self.boxesPath, component)

  def fetchBox(self, box):
    manifestURL = box.getRegistryURL()
    return Try.attempt(makeXHRRequest, url=manifestURL) >> defer(self.downloadBox, box=box)

  def downloadBox(self, boxResult, box):
    archiveURL = boxResult['archiveURL']
    archiveSHA = boxResult['archiveSHA1']

    logging.info("Downloading %s:%s (%s)" % (box.name, box.version, boxResult['archiveURL']))
    archive = os.path.join(self.boxesPath, box.getArchivePath())

    return Try.sequence([
      Shell.makeDirectory(os.path.dirname(archive)),
      Try.attempt(streamDownload, url=archiveURL, destination=archive) \
        .then(defer(self.verifyBoxArchive, expectedSHA=archiveSHA, archive=archive)),
      self.getDB().updateBoxRecord(box, boxResult)
    ])

  def verifyBoxArchive(self, expectedSHA, archive):
    logging.info("Verifying archive...")
    sha = sha1sum(archive)
    if sha == expectedSHA:
      return OK(sha)
    else:
      Try.attempt(lambda: os.remove(archive))
      return Fail(BoxArchiveHashMismatch("Box archive hash mismatch. Failed download?"))

  #-- Keys handling

  def getInsecureKeyFile(self):
    return getSupportFile('support/substance_insecure')

  def getInsecurePubKeyFile(self):
    return getSupportFile('support/substance_insecure.pub')
 
