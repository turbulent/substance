import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import FileSystemError

class Import(Command):

  def getShellOptions(self, optparser):
    #optparser.add_option("-v", dest="val", help="Single Val", default=False)
    #optparser.add_option("--longval", dest="longval", help="Long Val", default=False)
    #optparser.add_option("-b", dest="bool", help="Boolean", default=False, action="store_true")
    #optparser.add_option("--longbool", dest="longbool", help="Long Boolean", default=False, action="store_true")
    return optparser
 
  def main(self):

    name = self.args[0]
    engine = self.core.createEngine(name)
    vbox = VirtualBoxDriver(baseFolder=self.core.getEnginesPath())
    vbox.importMachine(name, "t/box.ovf", EngineProfile(cpus=2, memory=1024))
