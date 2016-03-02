import os
import re
import logging
from substance.shell import Shell
from substance.exceptions import ( SubstanceDriverError, VirtualBoxError )
import ConfigParser
import StringIO

class VirtualBoxDriver:
  '''
  Substance VirtualBox driver class. Interface to virtual box manager.
  '''

  VBOXMAN = "VBoxManage"

  def importMachine(self, name, ovfFile, engineProfile=None):
    '''
    Import a machine file. Return driver identifier of created virtual machine.
    '''

    # Dry run to find the information in the OVF and replace it with flags.
    try:
      ret = self.vboxManager("import", "-n %s" % ovfFile)
      ovfManifest = ret.get('stdout', '')
      logging.debug(ovfManifest)
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to import OVF: %s" % err)

    suggestedName = re.search(r'Suggested VM name "(.+?)"', ret.get('stdout'))
    if not suggestedName:
      raise SubstanceDriverError("Invalid OVF: File contains no VM Name.");
    else:
      suggestedName = suggestedName.group(1)

    logging.debug("OVF Suggested VM Name: %s" % suggestedName)

    profileParams = "--vsys 0 --vmname \"%s\"" % name
    if engineProfile:
      profileParams += " --cpus %d" % engineProfile.cpus
      profileParams += " --memory %d" % engineProfile.memory

    diskScan = re.compile(r'(\d+): Hard disk image: source image=.+, target path=(.+),')
    diskParams = ""
    for disk in diskScan.findall(ret.get('stdout')):
      diskPath = disk[1]
      diskPath = diskPath.rsplit(suggestedName, 1)
      diskPath = name.join(diskPath) 
      diskParams += "--unit %s --disk \"%s\"" % (disk[0], diskPath)
    
    try:
      self.vboxManager("import", "%s %s %s" % (ovfFile, profileParams, diskParams))
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to import machine \"%s\": %s" % (name, err.errorLabel))

    return self.getMachineID(name)

  def destroyMachine(self, uuid):
    '''
    Destroy the machine by driver identifier.
    '''
    try:
      self.vboxManager("unregistervm", "--delete \"%s\"" % (uuid))
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to destroy machine \"%s\": %s" % (uuid, err.errorLabel))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    try:
      self.vboxManager("startvm", "--type headless \"%s\"" % (uuid))
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to start machine \"%s\": %s" % (uuid, errorLabel))

    return True

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    try:
      self.vboxManager("controlvm", "\"%s\" savestate" % uuid)
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to suspend machine \"%s\": %s" % (uuid, err.errorLabel))

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    try:
      self.vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid)
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to halt machine \"%s\": %s" % (uuid, err.errorLabel))

  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    try:
      self.vboxManager("controlvm", "\"%s\" poweroff" % uuid)
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to halt machine \"%s\": %s" % (uuid, err.errorLabel))
      
  def getMachineInfo(self, uuid):
    '''
    Retrieve the machine info from the driver.
    '''
    try:
      ret = self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid)
      machInfo = ret.get('stdout', '')
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to fetch machine \"%s\" info: %s" % (uuid, err.errorLabel))

    return self.parseMachineInfo(machInfo)

  def getMachines(self):
    '''
    Retrive the list of machines and their driver identifiers.
    '''
    try:
      machines = []
      ret = self.vboxManager("list", "vms")
      matcher = re.compile(r'"([^"]+)" {([^}]+)}')

      for line in ret.get('stdout', '').split("\n"):
        parts = matcher.match(line)
        if parts:
          machines.append({'name':parts.group(1), 'id':parts.group(2)})
      return machines

    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to fetch machines list from Virtual Box: %s" % err.errorLabel)

  def getMachineID(self, name):
    '''
    Retrieve the driver specific machine ID.
    '''
    try:
      ret = self.vboxManager("list", "vms")
      matcher = re.compile('^"' + name + '" {([^}]+)}')
      parts = matcher.search(ret.get('stdout',''))
      if parts:
        return parts.group(1)
    except VirtualBoxError as err:
      raise SubstanceDriverError("Failed to fetch machines list from Virtual Box: %s" % err.errorLabel)
 
  def vboxManager(self, cmd, params):
    '''
    Invoke the VirtualBoxManager
    '''
    ret = Shell.procCommand("%s %s %s" % (self.VBOXMAN, cmd, params))
    if ret.get('returnCode'):
      raise VirtualBoxError(ret.get('stderr'))
    return ret

  def parseMachineInfo(self, machInfo):
    '''
    Parse Virtual Box machine info into a dict.
    '''
    lines = machInfo.split("\n")
    machDict = {}
    for line in lines:
      try:
        var, value = line.split("=", 1)
        value = value.strip()
        machDict[var] = value 
      except ValueError as err:
        pass
    return machDict
