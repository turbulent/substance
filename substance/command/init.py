import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.exceptions import EngineExistsError

class Init(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("--projects", dest="projects", help="Path to projects director")
    optparser.add_option("--mount", dest="mounts", help="Mount host path to engine path", nargs=10)
    optparser.add_option("--driver", dest="driver", help="Virtualization driver for this engine")
    optparser.add_option("--memory", type="int", dest="memory", help="Machine memory allocation")
    optparser.add_option("--cpus", type="int", dest="cpus", help="Machine vCPU allocation")
    return optparser
 
  def main(self):

    name = self.args[0]
    try:
      engineConfig = {}
      if self.options.driver:
        if not self.core.validDriver(self.options.driver):
          return self.exitError("Driver %s is not valid." % self.options.driver)
        engineConfig.set('driver', self.options.driver)

      if self.options.projects:
        if not os.path.isdir(self.options.projects):
          return self.exitError("Projects path %s does not exist." % self.options.projects)
       
      engineProfile = EngineProfile()
      if self.options.memory:
        engineProfile.memory = self.options.memory
      if self.options.cpus:
        engineProfile.cpus = self.options.cpus

      self.core.createEngine(name, config=engineConfig, profile=engineProfile)
    except EngineExistsError:
      logging.info("Engine \"%s\" already exists." % name) 
