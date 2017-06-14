import logging
from substance.logs import DriverLogAdapter

logger = logging.getLogger(__name__)

class Driver(object):
  '''
  Substance virtualization driver abstract
  '''

  def __init__(self, core):
    self.core = core
    self.logAdapter = DriverLogAdapter(logger, {'name': self.__class__.__name__})
 
  def importMachine(self, name, ovfFile, engineProfile=None):
    '''Import a machine image into a virtual machine'''
    raise NotImplementedError()

  def deleteMachine(self, uuid):
    '''Delete a virtual machine by driver id'''
    raise NotImplementedError()

  def startMachine(self, uuid):
    '''Start a virtual machine by driver id'''
    raise NotImplementedError()

  def suspendMachine(self, uuid):
    '''Suspend a virtual machine by driver id'''
    raise NotImplementedError()

  def haltMachine(self, uuid):
    '''Safely halt a virtual machine by driver id'''
    raise NotImplementedError()

  def terminateMachine(self, uuid):
    '''Forcefully terminate a virtual machine by driver id'''
    raise NotImplementedError()

  def getMachines(self):
    '''
    Get a list of virtual machines available from this driver.
    Form is a [dict(name:uuid)]
    '''
    raise NotImplementedError()

  def getMachineID(self, name):
    '''Retrieve the driver identifier for a machine name'''
    raise NotImplementedError()

  def getMachineState(self, uuid):
    '''Get the substance engine state for a virtual machine by driver id'''
    raise NotImplementedError()

  def exists(self, uuid):
    '''Check for existence of a virtual machine by driver id'''
    raise NotImplementedError()

  def isRunning(self, uuid):
    '''Check for that a virtual machine is running by driver id'''
    raise NotImplementedError()

  def isStopped(self, uuid):
    '''Check for that a virtual machine is stopped by driver id'''
    raise NotImplementedError()

  def isSuspended(self, uuid):
    '''Check for that a virtual machine is suspended by driver id'''
    raise NotImplementedError()
