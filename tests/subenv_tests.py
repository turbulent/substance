from builtins import range
import unittest
import os
import tempfile
import tests
import random
import string
from substance.monads import *
from substance import (Core, EngineProfile, Engine, Shell)
from substance.utils import writeToFile, parseDotEnv, readDotEnv

from substance.subenv import (SPECDIR, ENVFILE, CODELINK)
from substance.subenv import SubenvAPI

class TestSubenv(tests.TestBase):

  def setUp(self):
    self.basePath = self.addTemporaryDir() 
    self.projectsBasePath = self.addTemporaryDir() 
    self.subenvBasePath = self.addTemporaryDir() 
    
  def tearDown(self):
    pass
    if self.basePath:
      Shell.nukeDirectory(self.basePath).catch(tests.TestBase.raiser)
    if self.subenvBasePath:
      Shell.nukeDirectory(self.subenvBasePath).catch(tests.TestBase.raiser)
    if self.projectsBasePath:
      Shell.nukeDirectory(self.projectsBasePath).catch(tests.TestBase.raiser)

  def setUpDefaultCore(self):
    self.core = Core(basePath=self.basePath)
    self.assertIsInstance(self.core.initialize(), OK)
    self.api = SubenvAPI(self.subenvBasePath)
    self.assertIsInstance(self.api.initialize(), OK)
    return self.core
   
  def makeEnv(self):

    name = self.randString()

    ppath = os.path.join(self.projectsBasePath, name)
    specpath = os.path.join(ppath, SPECDIR)

    op = Shell.makeDirectory(ppath) \
      .then(defer(Shell.makeDirectory, specpath)) 

    self.assertIsInstance(op, OK)


    dirs = ['conf', os.path.join('conf','web'), os.path.join('conf','cron'), os.path.join('conf','logrotate')]
    ops = [ Try.attempt(Shell.makeDirectory, os.path.join(specpath, x)) for x in dirs ]   

    self.assertIsInstance(Try.sequence(ops), OK)

    tpl1 = "{{SUBENV_ENVPATH}}\n{{SUBENV_BASEPATH}}"
    tpl2 = 'This is a template with no vars.'

    customVar = self.randString()

    envTpl = 'name="%(name)s"\ncustom="%(custom)s"'

    filedata = {}
    filedata[ENVFILE] = envTpl % {'name': name, 'custom': customVar}
    filedata["tpl1.jinja"] = tpl1
    filedata[os.path.join("conf", "tpl2.jinja")] = tpl2

    ops = []
    for file, data in filedata.items():
       ops.append( Try.attempt(writeToFile, os.path.join(specpath, file), data) )
 
    self.assertIsInstance(Try.sequence(ops), OK)

    return {'name': name, 'custom': customVar, 'path': ppath, 'files': filedata, 'dirs': dirs}

 
  def testInit(self):
    self.setUpDefaultCore()
    self.env = self.makeEnv()

    custom2 = self.randString()
    op = self.api.init(self.env['path'], {'custom2': custom2})
    self.assertIsInstance(op, OK)

    envPath = os.path.join(self.subenvBasePath, "envs", self.env['name'])

    self.assertTrue(os.path.isdir(envPath))

    for f,fd in self.env['files'].items():
      root, ext = os.path.splitext(f)
      if ext == '.jinja':
        self.assertTrue(os.path.isfile(os.path.join(envPath, root)))
      elif f == ENVFILE:
        self.assertTrue(os.path.isfile(os.path.join(envPath, f)))
        data = readDotEnv(os.path.join(envPath, f))
        self.assertEqual(data['name'], self.env['name'])
        self.assertEqual(data['custom'], self.env['custom'])
        self.assertEqual(data['custom2'], custom2)
        self.assertEqual(data['SUBENV_NAME'], self.env['name'])
        self.assertEqual(data['SUBENV_BASEPATH'], os.path.join(self.projectsBasePath, self.env['name']))
        self.assertEqual(data['SUBENV_SPECPATH'], os.path.join(self.projectsBasePath, self.env['name'], SPECDIR))
      else:
        self.assertTrue(os.path.isfile(os.path.join(envPath, f)))
        with open(os.path.join(envPath, f), 'r') as fh:
          data = fh.read()
        self.assertEqual(fd, data)

    for d in self.env['dirs']:
      self.assertTrue(os.path.isdir(os.path.join(envPath, d)))

    ls = self.api.ls()
    self.assertIsInstance(ls, OK)
    ls = ls.getOK()
    names = [x.name for x in ls]
    self.assertIn(self.env['name'], names)

    op = self.api.delete(self.env['name'])
    self.assertIsInstance(op, OK)

    ls = self.api.ls()
    self.assertIsInstance(ls, OK)
    ls = ls.getOK()
    names = [x.name for x in ls]
    self.assertNotIn(self.env['name'], names)

  def randString(self):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
