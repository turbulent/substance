import re
from collections import OrderedDict
from substance.logs import *
from substance.monads import *
from substance.driver import Driver
from substance.constants import (EngineStates)

from vbox import (vboxManager)
import network
import machine
from exceptions import *

from netaddr import (IPAddress, IPNetwork)

class VirtualBoxDriver(Driver):
  '''
  Substance VirtualBox driver class. Interface to virtual box manager.
  '''

#  def readNetworkConfig(self): 
#    interface = self.engine.core.config.get('network', {}) \
#      .get('virtualbox', {}) \
#      .get('interface', None)
#
#    netrange = IPNetwork(self.engine.core.config.get('network').get('range'))
#    netconfig = {
#      'gateway': netrange[1],
#      'netmask': netrange.netmask,
#      'lowerIP': netrange[2],
#      'upperIP': netrange[-1]
#    }
#
#    return OK(netconfig)
#
#  def assertNetwork(self):
#
#    # Look in our config for an interface, if found, load it. If not found, create new.
#    # Assert the configuration of the found interface.
#      # If the ipconfig is wrong ; create a new interface.
#      # If the DHCP config for the interface does not match : Ensure it does.
#    # If no interface defined, create a new one.
# 
#    if interface:
#      return network.readHostOnlyInterface(interface) \
#        .catch(lambda err: self.provisionNetwork(netconfig)) \
#        .bind(self.assertNetwork, config=netconfig)
#    else:
#      return self.provisionNetwork(netconfig)
# 
#  def assertNetwork(self, hoif, netconfig):
#    if hoif.ip != netconfig['gateway']:
#      logging.warn("VirtualBox interface \"%s\" is not properly configured. Creating a new host-only network.")
#      return self.provisionNetwork(netconfig)
#    elif not hoif.dhcpEnabled:
#      logging.warn("VirtualBox interface \"%s\" does not have DHCP enabled. Re-Establishing now.")
#      return self.provisionNetworkDHCP(hoif.name, netconfig)
#    return OK(hoif)
# 
#  def provisionNetwork(self, netconfig):
#    ifm = network.addHostOnlyInterface() 
#    if ifm.isFail():
#      return ifm
#    iface = ifm.getOK()
#
#    return network.configureHostOnlyInterface, ip=netconfig['gateway'], netmask=netconfig['netmask']) \
#      .bid(defer(self.provisionNetworkDHCP(interface=iface, netconfig=netconfig)))
#
#  def provisionNetworkDHCP(self, interface, netconfig):
#    network.removeDHCP(interface).catch(lambda x: OK(interface)) \
#        .then(defer(addDHCP, **netconfig))
#
  
  def importMachine(self, name, ovfFile, engineProfile=None):
    return machine.inspectOVF(ovfFile) \
      .bind(defer(machine.makeImportParams, name=name, engineProfile=engineProfile)) \
      .bind(defer(machine.importOVF, ovfFile=ovfFile, name=name))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    return machine.start(uuid)

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    return machine.suspend(uuid)

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    return machine.halt(uuid)
    
  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    return machine.terminate(uuid)

  def deleteMachine(self, uuid):
    '''
    Delete the machine by driver identifier.
    '''
    return machine.delete(uuid)

  def exportMachine(self, uuid):
    #XXX To be implemented
    pass
 
  def getMachines(self):
    '''
    Retrieve the list of machines and their driver identifiers.
    '''
    return machine.readMachines()

  # -- Parse results from Virtual Box

  def getMachineID(self, name):
    '''
    Retrieve the driver specific machine ID for a machine name.
    '''
    return machine.findMachineID(name)

  def exists(self, uuid):
    '''
    Check in the driver that the specified identifier exists.
    '''
    return machine.readMachineExists(uuid)

  def isRunning(self, uuid):
    if self.getMachineState(uuid) is EngineStates.RUNNING:
      return True

  def isStopped(self, uuid):
    if self.getMachineState(uuid) is not EngineStates.RUNNING:
      return True

  def isSuspended(self, uuid):
    if self.getMachineState(uuid) is EngineStates.SUSPENDED:
      return True

  def getMachineState(self, uuid):
    '''
    Retrieve the Substance machine state for this driver id
    '''
    return machine.readMachineState(uuid) >> self.vboxStateToMachineState

  def vboxStateToMachineState(self, vboxState):
    '''
    Resolve a vbox machine state to a substance engine state.
    '''
    mapping = {
      "poweroff": EngineStates.STOPPED,
      "saved": EngineStates.SUSPENDED,
      "aborted": EngineStates.STOPPED,
      "paused": EngineStates.STOPPED,
      "stuck": EngineStates.STOPPED,
      "restoring": EngineStates.STOPPED,
      "snapshotting": EngineStates.STOPPED,
      "setting up": EngineStates.STOPPED,
      "online snapshotting": EngineStates.STOPPED,
      "restoring snapshot": EngineStates.STOPPED,
      "deleting snapshot": EngineStates.STOPPED,
      "running": EngineStates.RUNNING,
      "starting": EngineStates.RUNNING,
      "stopping" : EngineStates.RUNNING,
      "saving": EngineStates.RUNNING,
      "live snapshotting": EngineStates.RUNNING,
      "unknown": EngineStates.UNKNOWN,
      "inaccessible": EngineStates.INEXISTENT,
      "inexistent": EngineStates.INEXISTENT
    }
    state = mapping.get(vboxState, EngineStates.UNKNOWN)
    ddebug("Machine state: %s : %s", vboxState, state)
    return OK(state)


