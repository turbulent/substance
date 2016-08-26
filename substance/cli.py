from __future__ import absolute_import
import sys
import logging
from collections import OrderedDict
from substance import (Program, Core)
from substance.utils import getPackageVersion
import substance.command
import substance.logs

class SubstanceCLI(Program):
  """Substance CLI command"""

  def __init__(self):
    super(SubstanceCLI, self).__init__()
    self.name = 'substance'

  def setupCommands(self):
    self.addCommand('use', 'substance.command.use')
    self.addCommand('launch', 'substance.command.launch')
    self.addCommand('suspend', 'substance.command.suspend')
    self.addCommand('halt', 'substance.command.halt')
    self.addCommand('switch', 'substance.command.switch')
    self.addCommand('start', 'substance.command.start')
    self.addCommand('stop', 'substance.command.stop')
    self.addCommand('restart', 'substance.command.restart')
    self.addCommand('recreate', 'substance.command.recreate')
    self.addCommand('ssh', 'substance.command.ssh')
    self.addCommand('status', 'substance.command.status')
    self.addCommand('logs', 'substance.command.logs')
    #self.addCommand('docker', 'substance.command.docker')
    #self.addCommand('exec', 'substance.command.exec')
    self.addCommand('engine', 'substance.command.engine')
    return self

  def getShellOptions(self, optparser):
    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "substance [options] COMMAND [command-options]"

  def getHelpTitle(self):
    version = getPackageVersion()
    return "Local docker-based development environments (version: %s)" % version

  def initCommand(self, command):
    core = Core()
    if self.getOption('assumeYes'):
      core.setAssumeYes(True)

    core.initialize().catch(self.exitError)

    command.core = core
    return command

def cli():
  args = sys.argv[1:]
  prog = SubstanceCLI()
  prog.execute(args)
