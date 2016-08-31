import unittest
import os
import tempfile
import tests
import re
from substance.core import Core
from substance.engine import (EngineProfile, Engine)
from substance.shell import Shell
from substance.monads import *
from substance.constants import *

class TestEngine(tests.TestBase):

  core = None
  engine = None
  basePath = None
  projectsPath = None

  vmTest = True

  @classmethod
  def setUpClass(cls):
    cls.basePath = cls.addTemporaryDir()
    cls.projectsPath = cls.addTemporaryDir()

    cls.core = Core(basePath=cls.basePath)
    cls.core.initialize().catch(cls.raiser)

    cls.engine = cls.core.createEngine("testEngine", config={"driver":"virtualbox","projectsPath":cls.projectsPath})  \
      .bind(Engine.loadConfigFile)  \
      .catch(TestEngine.raiser) \
      .getOK()
     
  @classmethod
  def tearDownClass(cls):
    if cls.engine and cls.engine.isProvisioned():
      cls.engine.deprovision()

    if cls.basePath:
      Shell.nukeDirectory(cls.basePath).catch(cls.raiser)
    if cls.projectsPath:
      Shell.nukeDirectory(cls.projectsPath).catch(cls.raiser)

  def testInitSequence(self):
    if not self.vmTest:
      return
    self.doProvision()
    self.doStart()
    self.doSuspend()
    self.doRestart()
    self.doDeprovision()
    
  def testLaunch(self):
    if not self.vmTest:
      return
    self.doLaunch()
  
  def doProvision(self):
    op = self.engine.provision()
    self.assertIsInstance(op, OK)
    self.assertTrue(self.engine.isProvisioned())
    self.assertIsNotNone(self.engine.getDriverID())
    self.checkStateMatch(EngineStates.STOPPED)

  def doStart(self):
    op = self.engine.start()
    self.assertIsInstance(op, OK)
    self.checkStateMatch(EngineStates.RUNNING)

  def doSuspend(self):
    op = self.engine.suspend() 
    self.assertIsInstance(op, OK)
    self.checkStateMatch(EngineStates.SUSPENDED)

  def doRestart(self):
    op = self.engine.start()
    self.assertIsInstance(op, OK)
    self.checkStateMatch(EngineStates.RUNNING)

  def doDeprovision(self):
    op = self.engine.deprovision()
    self.assertIsInstance(op, OK)
    self.assertFalse(self.engine.isProvisioned())
    self.assertIsNone(self.engine.getDriverID())
    self.checkStateMatch(EngineStates.INEXISTENT)

  def doLaunch(self):
    op = self.engine.launch()
    self.assertIsInstance(op, OK)

  def checkStateMatch(self, stateMatch):
    state = self.engine.fetchState()
    self.assertIsInstance(state, OK)
    self.assertEqual(state.getOK(), stateMatch)
