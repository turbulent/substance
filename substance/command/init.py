import os
from substance.logs import *
from substance.command import Command
from substance.box import Box
from substance.engine import EngineProfile
from substance.exceptions import (InvalidOptionError)

class Init(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("--projects", dest="projects", help="Path to projects director")
    optparser.add_option("--mount", dest="mounts", help="Mount host path to engine path", nargs=10)
    optparser.add_option("--driver", dest="driver", help="Virtualization driver for this engine")
    optparser.add_option("--memory", type="int", dest="memory", help="Machine memory allocation")
    optparser.add_option("--cpus", type="int", dest="cpus", help="Machine vCPU allocation")
    optparser.add_option("--box", type="str", dest="box", help="Engine box image")
    return optparser

  def main(self):

    name = self.getInputName()
  
    options = self.buildConfigFromArgs().bind(self.buildProfileFromArgs) \
      .catch(self.exitError).getOK()

    self.core.initialize() \
      .then(defer(self.core.createEngine, name, config=options['config'], profile=options['profile'])) \
      .bind(dinfo("Engine \"%s\" has been created", name)) \
      .catch(self.exitError) \

  def buildConfigFromArgs(self, config={}):
    opts = {}

    boxName = self.core.getDefaultBoxString() if not self.options.box else self.options.box
    box = self.core.getBox(boxName)
    if box.isFail():
      return box
    opts['box'] = box.getOK().get('boxstring')

    if self.options.driver:
      if not self.validateDriver(self.options.driver):
        return Fail(InvalidOptionError("Driver %s is not valid." % self.options.driver))
      opts['driver'] = self.options.driver

    if self.options.projects:
      if not os.path.isdir(self.options.projects):
        return Fail(InvalidOptionError("Projects path %s does not exist." % self.options.projects))
      opts['projectsPath'] = self.options.driver

    config['config'] = opts
    return OK(config)

  def buildProfileFromArgs(self, config={}):
    profile = EngineProfile()
    if self.options.memory and self.validateInteger(self.options.memory):
      profile.memory = self.options.memory
    if self.options.cpus and self.validateInteger(self.options.cpus):
      profile.cpus = self.options.cpus
  
    config['profile'] = profile
    return OK(config)

