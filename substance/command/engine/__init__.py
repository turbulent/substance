from __future__ import absolute_import
import sys
import logging
from collections import OrderedDict
from substance import (SubProgram, Core)

class Engine(SubProgram):

  def __init__(self):
    super(Engine, self).__init__()

  def setupCommands(self):
    self.addCommand('ls', 'substance.command.engine.ls')
    self.addCommand('create', 'substance.command.engine.create')
    self.addCommand('delete', 'substance.command.engine.delete')
    self.addCommand('launch', 'substance.command.engine.launch')
    self.addCommand('halt', 'substance.command.engine.halt')
    self.addCommand('suspend', 'substance.command.engine.suspend')
    self.addCommand('deprovision', 'substance.command.engine.deprovision')
    self.addCommand('edit', 'substance.command.engine.edit')
    self.addCommand('ssh', 'substance.command.engine.ssh')
    self.addCommand('env', 'substance.command.engine.env')
    self.addCommand('sshinfo', 'substance.command.engine.sshinfo')
    self.addCommand('sync', 'substance.command.engine.sync')
    return self

  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "substance engine [options] COMMAND [command-options]"

  def getHelpTitle(self):
    return "Substance engine management"

  def initCommand(self, command):
    command.core = self.core
    return command
