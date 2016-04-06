import unittest
import os
import tempfile
import tests
from substance.core import Core
from substance.engine import (EngineProfile, Engine)
from substance.shell import Shell
from substance.monads import *

class TestCore(tests.TestBase):

  def setUp(self):
    self.basePath = self.addTemporaryDir() 
    self.projectsPath = self.addTemporaryDir() 
    
  def tearDown(self):
    if self.basePath:
      Shell.nukeDirectory(self.basePath).catch(TestCore.raiser)
    if self.projectsPath:
      Shell.nukeDirectory(self.projectsPath).catch(TestCore.raiser)

  def setUpDefaultCore(self):
    self.core = Core(basePath=self.basePath)
    self.assertIsInstance(self.core.initialize(), OK)
    return self.core
    
  def testInitialize(self):
    core = Core(basePath=self.basePath)
    self.assertIsInstance(core.initialize(), OK)
    self.assertEqual(core.getBasePath(), self.basePath)
    self.assertTrue(os.path.exists(self.basePath))
    self.assertTrue(os.path.exists(core.getBasePath()))
    self.assertTrue(os.path.exists(core.getEnginesPath()))
    self.assertTrue(os.path.exists(os.path.join(self.basePath, 'substance.yml')))
   
    core = Core(basePath=self.basePath, configFile="foobar.yml")
    self.assertIsInstance(core.initialize(), OK)
    self.assertTrue(os.path.exists(self.basePath))
    self.assertTrue(os.path.exists(os.path.join(self.basePath, 'foobar.yml')))
   
 
  def testDefaultConfig(self):
    self.setUpDefaultCore()
    self.assertIsNotNone(self.core.config)
    self.assertEqual(self.core.config.get('assumeYes', None), False)
    self.assertEqual(self.core.config.get('basePath', None), self.basePath)

  def testConfig(self):
    self.setUpDefaultCore()
    self.assertEqual(self.core.config.set("foo", "bar"), "bar")
    self.assertEqual(self.core.config.get("foo", None), "bar")
    self.assertIsInstance(self.core.config.saveConfig(), OK)
    self.assertIsInstance(self.core.config.loadConfigFile(), OK)
    self.assertEqual(self.core.config.get("foo", None), "bar")

  def coreTestEngines(self):
    self.setUpDefaultCore()
    self.assertEqual(self.core.config.set("assumeYes", True), True)

    engines = self.core.getEngines()
    self.assertIsInstance(engines, OK)
    self.assertEqual(engines.getOK(), [])
 
  def testCreateEngine(self):
    self.setUpDefaultCore()
    createOp =self.core.createEngine("coreTestEngine", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp, OK)


    engine = self.core.loadEngine("coreTestEngine")
    self.assertIsInstance(engine, OK)

    self.assertEqual(os.path.join(self.core.getEnginesPath(), "coreTestEngine"), engine.getOK().getEnginePath())
    self.assertTrue(engine.getOK().getEnginePath(), "coreTestEngine")

    engine = engine.bind(Engine.loadConfigFile)
    self.assertIsInstance(engine, OK)

    engine = engine.getOK()

    self.assertEqual(engine.config.get('projectsPath'), self.projectsPath)
    self.assertEqual(engine.config.get('profile').get('cpus'), 4)
    self.assertEqual(engine.config.get('profile').get('memory'), 512)

  def testGetEngines(self):
    self.setUpDefaultCore()
    createOp =self.core.createEngine("coreTestEngine", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp, OK)
    createOp2 =self.core.createEngine("coreTestEngine2", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp2, OK)
    createOp3 =self.core.createEngine("coreTestEngine3", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp3, OK)

    engines = self.core.getEngines()
    self.assertIsInstance(engines, OK)
    self.assertEqual(len(engines.getOK()), 3)
    self.assertEqual(engines.getOK(), ['coreTestEngine','coreTestEngine2','coreTestEngine3'])

  def testRemoveEngine(self):
    self.setUpDefaultCore()
    createOp =self.core.createEngine("coreTestEngine", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp, OK)
    createOp2 =self.core.createEngine("coreTestEngine2", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp2, OK)
    createOp3 =self.core.createEngine("coreTestEngine3", config={"projectsPath":self.projectsPath}, profile=EngineProfile(cpus=4, memory=512))
    self.assertIsInstance(createOp3, OK)

    engines = self.core.getEngines()
    self.assertIsInstance(engines, OK)

    self.core.removeEngine("coreTestEngine2")

    self.assertTrue(not os.path.exists(os.path.join(self.core.getEnginesPath(), "coreTestEngine2")))

    engines = self.core.getEngines()
    self.assertIsInstance(engines, OK)
    self.assertEqual(len(engines.getOK()), 2)
    self.assertEqual(engines.getOK(), ['coreTestEngine','coreTestEngine3'])

  def testKeys(self):
    self.setUpDefaultCore()
    k = self.core.getInsecureKeyFile()
    self.assertTrue(os.path.exists(k))

    k = self.core.getInsecurePubKeyFile()
    self.assertTrue(os.path.exists(k))
