import re
from collections import OrderedDict
from substance.logs import *
from substance.monads import *
from substance.driver import Driver
from substance.constants import (EngineStates)

from vbox import (vboxManager)
import network
import machine

class VirtualBoxDriver(Driver):
  '''
  Substance VirtualBox driver class. Interface to virtual box manager.
  '''

  def importMachine(self, name, ovfFile, engineProfile=None):
    return machine.inspectOVF(ovfFile) \
      .bind(defer(machine.makeImportParams, name=name, engineProfile=engineProfile)) \
      .bind(defer(machine.importOVF, ovfFile=ovfFile, name=name))

  def deleteMachine(self, uuid):
    '''
    Delete the machine by driver identifier.
    '''
    return vboxManager("unregistervm", "--delete \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    return vboxManager("startvm", "--type headless \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    return vboxManager("controlvm", "\"%s\" savestate" % uuid) \
      .bind(lambda x: OK(uuid))

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    return vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid) \
      .bind(lambda x: OK(uuid))
    
  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    return vboxManager("controlvm", "\"%s\" poweroff" % uuid) \
      .bind(lambda x: OK(uuid))

  def exportMachine(self, uuid):
    #XXX To be implemented
    pass
 
  def getMachines(self):
    '''
    Retrive the list of machines and their driver identifiers.
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


