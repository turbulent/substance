from __future__ import print_function
from substance.monads import *
from substance.logs import *
from substance import (Engine, Command)
from substance.exceptions import (SubstanceError)

class Sshinfo(Command):

  def getUsage(self):
    return "substance sshinfo [ENGINE NAME]"
  
  def getHelpTitle(self):
    return "Obtain the ssh info configuration for connecting to an engine"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):

    name = self.getInputName()

    self.core.loadEngine(name) \
      .bind(Engine.loadConfigFile) \
      .bind(self.outputSSHInfo) \
      .catch(self.exitError)

  def outputSSHInfo(self, engine):
    host = engine.getSSHIP()
    port = engine.getSSHPort()
   
    sshconfig = """Host %(name)s
  HostName %(host)s
  User substance
  Port %(port)s
  UserKnownHostsFile /dev/null
  IdentityFile "%(keyfile)s"
  StrictHostKeyChecking no
  PasswordAuthentication no
  LogLevel FATAL
  ForwardAgent yes""" 
  
    sshconfig = sshconfig % ({
        'name': engine.name,
        'host': host, 
        'port': port,  
        'keyfile': self.core.getInsecureKeyFile()
      })

    print(sshconfig)
    return OK(sshconfig)
