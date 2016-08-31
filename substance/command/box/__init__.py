from __future__ import absolute_import
import sys
import logging
from collections import OrderedDict
from substance import (SubProgram, Core)

class Box(SubProgram):

  def __init__(self):
    super(Box, self).__init__()

  def setupCommands(self):
    self.addCommand('ls', 'substance.command.box.ls')
    self.addCommand('pull', 'substance.command.box.pull')
    self.addCommand('delete', 'substance.command.box.delete')
    return self

  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "substance box [options] COMMAND [command-options]"

  def getHelpTitle(self):
    return "Substance box management"

  def initCommand(self, command):
    command.core = self.core
    return command
