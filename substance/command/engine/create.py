import os
from substance.logs import *
from substance import (Command, Box, EngineProfile)
from substance.exceptions import (InvalidOptionError)

class Create(Command):

  def getUsage(self):
    return "substance engine init [options] [ENGINE NAME]"

  def getHelpTitle(self):
    return "Create a new engine configuration"

  def getShellOptions(self, optparser):
    optparser.set_description("Create a new substance engine")
    optparser.add_option("--devroot", dest="devroot", help="Path to local devroot directory.")
    optparser.add_option('--devroot-mode', dest="devroot_mode", help="devroot sync mode", default="unison")
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

    self.core.createEngine(name, config=options['config'], profile=options['profile']) \
      .bind(dinfo("Engine \"%s\" has been created", name)) \
      .catch(self.exitError) \

  def buildConfigFromArgs(self, config={}):
    opts = {}

    boxName = self.core.getDefaultBoxString() if not self.options.box else self.options.box
    box = self.core.readBox(boxName)
    if box.isFail():
      return box
    opts['box'] = box.getOK().boxstring

    if self.options.driver:
      if not self.validateDriver(self.options.driver):
        return Fail(InvalidOptionError("Driver %s is not valid." % self.options.driver))
      opts['driver'] = self.options.driver

    if self.options.devroot:
      if not os.path.isdir(self.options.devroot):
        return Fail(InvalidOptionError("Devroot path %s does not exist." % self.options.devroot))
      opts['devroot'] = {} if 'devroot' not in opts else opts['devroot']
      opts['devroot']['path'] = self.options.devroot

    if self.options.devroot_mode:
      #XXX Fix hardcoded values.
      if self.options.devroot_mode not in ['rsync','sharedfolder','unison']:
        return Fail(InvalidOptionError("Devroot mode '%s' is not valid."))
      opts['devroot'] = {} if 'devroot' not in opts else opts['devroot']
      opts['devroot']['mode'] = self.options.devroot_mode
      
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

