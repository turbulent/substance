import logging
from substance.command import Command
from substance.engine import Engine
from substance.monads import *
from substance.logs import *

from substance.driver.virtualbox.machine import *
from substance.driver.virtualbox.network import *

class Testcom(Command):

  vboxManager = None
  vbox = None

  def getShellOptions(self, optparser):
    optparser.add_option("-v", dest="val", help="Single Val", default=False)
    optparser.add_option("--longval", dest="longval", help="Long Val", default=False)
    optparser.add_option("-b", dest="bool", help="Boolean", default=False, action="store_true")
    optparser.add_option("--longbool", dest="longbool", help="Long Boolean", default=False, action="store_true")
    return optparser

  def main(self):
    logging.info("Test command!")
    logging.debug("Input: %s", self.input)
    logging.debug("Options: %s", self.options)
    logging.debug("Args: %s", self.args)

    name = self.getInputName()

    self.core.initialize()  \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) \
      .bind(self.printEngineInfo)  \
      .bind(self.printPortForwards)  \
      .bind(self.clearPortForwards) \
      .bind(self.printPortForwards)  \
      .bind(self.addPortForwards) \
      .bind(self.printPortForwards)  \
      .catch(self.exitError)


  def printEngineInfo(self, engine):

    driver = engine.getDriver()
    machInfo = readMachineInfo(engine.getDriverID()).catch(self.exitError).getOK()

    for k,v in machInfo.iteritems():
      print("%s = %s" % (k,v))

    return OK(engine) 

  def printPortForwards(self, engine):

    driver = engine.getDriver()
    ports = readPortForwards(engine.getDriverID()) \
      .catch(self.exitError).getOK()

    for port in ports:
      print("%s" % port)

    return OK(engine) 

  def clearPortForwards(self, engine):
    driver = engine.getDriver()
    clear = clearAllPortForwards(engine.getDriverID()) \
      .catch(self.exitError).getOK()
    return OK(engine) 
 
  def addPortForwards(self, engine):
    ports = [
      PortForward("substance-ssh", 1, "tcp", "", 4500, "", 22),
      PortForward("Bogus port", 1, "tcp", "", 34252, "", 200),
      PortForward("docker-daemon", 1, "tcp", "", 3232, "", 2375),
    ] 
    return addPortForwards(ports, engine.getDriverID()) \
      .then(lambda: OK(engine))

  def printNetworks(self, engine):

    driver = engine.getDriver()
    nets = readNetworks()  \
      .catch(self.exitError).getOK()

    for net in nets:
      print("%s" % net)

    return OK(engine)

  
