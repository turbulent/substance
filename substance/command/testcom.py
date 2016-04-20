import logging
import pprint
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

    engine = self.core.initialize()  \
      .then(defer(self.core.loadEngine, name)) \
      .bind(Engine.loadConfigFile) 

    if engine.isFail():
      return self.exitError(engine)
    engine = engine.getOK()

    return engine.shell()

  def debugPrint(self, x):
    pprint.pprint(x)
    return x

  def testConnect(self, engine):
    pass

  def addFolder(self, engine):
    folder = machine.SharedFolder("tmp", "/tmp")
    return machine.addSharedFolder(folder, engine.getDriverID())

  def addFolders(self, engine):
    folders = [
      machine.SharedFolder("bbeausej", "/Users/bbeausej"),
      machine.SharedFolder("tmp", "/tmp")
    ]

    return machine.addSharedFolders(folders, engine.getDriverID())
 
  def clearFolders(self, engine):
    return machine.clearSharedFolders(engine.getDriverID())

  def readFolders(self, engine):
    return machine.readSharedFolders(engine.getDriverID())

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

  def printDHCPs(self, engine):

    driver = engine.getDriver()
    nets = readDHCPs()  \
      .catch(self.exitError).getOK()

    for net in nets:
      print("%s" % net)

    return OK(engine)

 
  def addDHCP(self, engine):
    net = DHCP(
      interface="vboxnet7",
      serverName="HostInterfaceDHCPing-vboxnet7",
      gateway="178.1.1.1",
      mask="255.255.255.0",
      lowerIP="178.1.1.100",
      upperIP="178.1.1.150",
      enabled="Yes"
    )
    return addDHCP(net).then(lambda: OK(engine))

  def removeDHCP(self, engine):
    return readDHCP("vboxnet7").bind(removeDHCP).then(lambda: OK(engine))
    
  def printHOIFs(self, engine):
    hoifs = readHostOnlyInterfaces().catch(self.exitError).getOK()
    for hoif in hoifs:
      print("%s" % hoif)
