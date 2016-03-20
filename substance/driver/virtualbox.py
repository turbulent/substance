import re
from substance.logs import *
from substance.monads import *
from substance.driver import Driver
from substance.shell import Shell
from substance.constants import (EngineStates)
from substance.exceptions import (
  SubstanceDriverError,
  VirtualBoxError, 
  ShellCommandError
)

class VirtualBoxDriver(Driver):
  '''
  Substance VirtualBox driver class. Interface to virtual box manager.
  '''

  VBOXMAN = "VBoxManage"

  def importMachine(self, name, ovfFile, engineProfile=None):
    '''
    Import a machine file. Return driver identifier of created virtual machine.
    '''
    return self.inspectOVF(ovfFile) \
      .bind(defer(self.makeImportParams, name=name, engineProfile=engineProfile)) \
      .bind(defer(self.importOVF, ovfFile=ovfFile, name=name))

  def inspectOVF(self, ovfFile):
    return self.vboxManager("import", "-n %s" % ovfFile) 
    
  def makeImportParams(self, inspection, name, engineProfile=None):

    suggestedName = re.search(r'Suggested VM name "(.+?)"', inspection)
    if not suggestedName:
      return Fail(SubstanceDriverError("Invalid OVF: File contains no VM Name"))
    else:
      suggestedName = suggestedName.group(1)

    ddebug("OVF Suggested VM Name \"%s\"", name)

    importParams = ["--vsys 0 --vmname \"%s\"" % name]
    if engineProfile:
      importParams.append("--cpus %d" % engineProfile.cpus)
      importParams.append("--memory %d" % engineProfile.memory)

    diskScan = re.compile(r'(\d+): Hard disk image: source image=.+, target path=(.+),')
    for disk in diskScan.findall(inspection):
      diskPath = disk[1]
      diskPath = diskPath.rsplit(suggestedName, 1)
      diskPath = name.join(diskPath)
      importParams.append("--unit %s --disk \"%s\"" % (disk[0], diskPath))

    return OK(importParams)

  def importOVF(self, importParams, name, ovfFile):
    importParams.insert(0, ovfFile)
    return self.vboxManager("import", " ".join(importParams)) \
      .then(defer(self.getMachineID, name))

#    try:
#      self.vboxManager("import", "%s %s %s" % (ovfFile, profileParams, diskParams))
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to import machine \"%s\": %s" % (name, err.errorLabel))
#
#    return self.getMachineID(name)


#    # Dry run to find the information in the OVF and replace it with flags.
#    try:
#      ret = self.vboxManager("import", "-n %s" % ovfFile)
#      ovfManifest = ret.get('stdout', '')
#      logging.debug(ovfManifest)
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to import OVF: %s" % err)
#
#    suggestedName = re.search(r'Suggested VM name "(.+?)"', ret.get('stdout'))
#    if not suggestedName:
#      raise SubstanceDriverError("Invalid OVF: File contains no VM Name")
#    else:
#      suggestedName = suggestedName.group(1)
#
#    logging.debug("OVF Suggested VM Name: %s", suggestedName)
#
#    profileParams = "--vsys 0 --vmname \"%s\"" % name
#    if engineProfile:
#      profileParams += " --cpus %d" % engineProfile.cpus
#      profileParams += " --memory %d" % engineProfile.memory
#
#    diskScan = re.compile(r'(\d+): Hard disk image: source image=.+, target path=(.+),')
#    diskParams = ""
#    for disk in diskScan.findall(ret.get('stdout')):
#      diskPath = disk[1]
#      diskPath = diskPath.rsplit(suggestedName, 1)
#      diskPath = name.join(diskPath)
#      diskParams += "--unit %s --disk \"%s\"" % (disk[0], diskPath)
#
#    try:
#      self.vboxManager("import", "%s %s %s" % (ovfFile, profileParams, diskParams))
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to import machine \"%s\": %s" % (name, err.errorLabel))
#
#    return self.getMachineID(name)

  def deleteMachine(self, uuid):
    '''
    Delete the machine by driver identifier.
    '''
    return self.vboxManager("unregistervm", "--delete \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

#    try:
#      self.vboxManager("unregistervm", "--delete \"%s\"" % (uuid))
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to delete machine \"%s\": %s" % (uuid, err.errorLabel))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    return self.vboxManager("startvm", "--type headless \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

#    try:
#      self.vboxManager("startvm", "--type headless \"%s\"" % (uuid))
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to start machine \"%s\": %s" % (uuid, err.errorLabel))
#
#    return True

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    return self.vboxManager("controlvm", "\"%s\" savestate" % uuid) \
      .bind(lambda x: OK(uuid))

#    try:
#      self.vboxManager("controlvm", "\"%s\" savestate" % uuid)
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to suspend machine \"%s\": %s" % (uuid, err.errorLabel))

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    return self.vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid) \
      .bind(lambda x: OK(uuid))
    
#    try:
#      self.vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid)
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to halt machine \"%s\": %s" % (uuid, err.errorLabel))

  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    return self.vboxManager("controlvm", "\"%s\" poweroff" % uuid) \
      .bind(lambda x: OK(uuid))

#    try:
#      self.vboxManager("controlvm", "\"%s\" poweroff" % uuid)
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to halt machine \"%s\": %s" % (uuid, err.errorLabel))

  def getMachineInfo(self, uuid):
    '''
    Retrieve the machine info from the driver.
    '''
    return self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
      .bind(self.parseMachineInfo)

#    try:
#      ret = self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid)
#      machInfo = ret.get('stdout', '')
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to fetch machine \"%s\" info: %s" % (uuid, err.errorLabel))
#
#    return self.parseMachineInfo(machInfo)

  def getMachines(self):
    '''
    Retrive the list of machines and their driver identifiers.
    '''
    self.vboxManager("list", "vms") >> self.parseMachinesList

  def parseMachinesList(self, vms):
      matcher = re.compile(r'"([^"]+)" {([^}]+)}')
      machines = {}
      for line in vms.split("\n"):
        parts = matcher.match(line)
        if parts:
          machines[parts.group(1)] = parts.group(2)
      return OK(machines)
    
#    try:
#      machines = []
#      ret = self.vboxManager("list", "vms")
#      matcher = re.compile(r'"([^"]+)" {([^}]+)}')
#
#      for line in ret.get('stdout', '').split("\n"):
#        parts = matcher.match(line)
#        if parts:
#          machines.append({'name':parts.group(1), 'id':parts.group(2)})
#      return machines
#
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to fetch machines list from Virtual Box: %s" % err.errorLabel)

  def getMachineID(self, name):
    '''
    Retrieve the driver specific machine ID.
    '''
    return self.vboxManager("list", "vms") \
      .bind(self.parseMachinesList) \
      .bind(lambda x: OK(x[name]) if name in x else Fail("No Machine ID found for \"%s\"" %name))

#    try:
#      ret = self.vboxManager("list", "vms")
#      parts = re.search(r'"' + re.escape(name) + '" {([^}]+)}', ret.get('stdout', ''), re.M)
#      if parts:
#        logging.debug("Machine ID for %s : %s", name, parts.group(1))
#        return parts.group(1)
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to fetch machines list from Virtual Box: %s" % err.errorLabel)

  def exists(self, uuid):
    '''
    Check in the driver that the specified identifier exists.
    '''
    return self.vboxManager("list", "vms") >> defer(self.parseMachinesForID, uuid=uuid)

  def parseMachinesForID(self, vms, uuid):
    if re.search(r'"([^"]+)" {'+re.escape(uuid)+'}', vms, re.M):
      return OK(True)
    else:
      return OK(False)
   
#    try:
#      ret = self.vboxManager("list", "vms")
#      parts = re.search(r'"([^"]+)" {'+re.escape(uuid)+'}', ret.get('stdout', ''), re.M)
#      if parts:
#        return True
#    except VirtualBoxError as err:
#      raise SubstanceDriverError("Failed to fetch machines list from Virtual Box: %s" % err.errorLabel)

  def parseMachineInfo(self, machInfo):
    '''
    Parse Virtual Box machine info into a dict.
    '''
    lines = machInfo.split("\n")
    machDict = {}
    for line in lines:
      try:
        var, value = line.split("=", 1)
        value = value.strip('"')
        machDict[var] = value
      except ValueError:
        pass
    return OK(machDict)

  def isRunning(self, uuid):
    if self.getMachineState(uuid) is EngineStates.RUNNING:
      return True

  def isStopped(self, uuid):
    if self.getMachineState(uuid) is not EngineStates.RUNNING:
      return True

  def isSuspended(self, uuid):
    if self.getMachineState(uuid) is EngineStates.SUSPENDED:
      return True

  def getInternalState(self, uuid):
    '''
    Retrieve the virtual box machine state
    '''
    return self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
      .catch(lambda err: OK("inexistent") if err.code is "VBOX_E_OBJECT_NOT_FOUND" else None) \
      .bind(defer(self.parseMachineState, uuid=uuid))

  def parseMachineState(self, vminfo, uuid):
      if re.search(r'^name="<inaccessible>"$', vminfo, re.M):
        return OK('inaccessible')
      
      stateMatch = re.search(r'^VMState="(.+?)"$', vminfo, re.M)
      if stateMatch:
        return OK(stateMatch.group(1))
      else:
        return OK('inexistent')
  
#    try:
#      ret = self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid)
#      machInfo = ret.get('stdout', '')
#      if re.search(r'^name="<inaccessible>"$', machInfo, re.M):
#        return 'inaccessible'
#      
#      stateMatch = re.search(r'^VMState="(.+?)"$', machInfo, re.M)
#      if stateMatch:
#        return stateMatch.group(1)
#
#    except VirtualBoxError as err:
#      if err.code == "VBOX_E_OBJECT_NOT_FOUND":
#        return "inexistent"
#      raise SubstanceDriverError("Failed to fetch machine \"%s\" info: %s" % (uuid, err.errorLabel))
#
#    return 'unknown'

  def getMachineState(self, uuid):
    '''
    Retrieve the Substance machine state for this driver id
    '''
    return self.getInternalState(uuid) >> self.vboxStateToMachineState

  def vboxStateToMachineState(self, vboxState):
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

#    vboxState = self.getInternalState(uuid)
#    mapping = {
#      "poweroff": EngineStates.STOPPED,
#      "saved": EngineStates.SUSPENDED,
#      "aborted": EngineStates.STOPPED,
#      "paused": EngineStates.STOPPED,
#      "stuck": EngineStates.STOPPED,
#      "restoring": EngineStates.STOPPED,
#      "snapshotting": EngineStates.STOPPED,
#      "setting up": EngineStates.STOPPED,
#      "online snapshotting": EngineStates.STOPPED,
#      "restoring snapshot": EngineStates.STOPPED,
#      "deleting snapshot": EngineStates.STOPPED,
#      "running": EngineStates.RUNNING,
#      "starting": EngineStates.RUNNING,
#      "stopping" : EngineStates.RUNNING,
#      "saving": EngineStates.RUNNING,
#      "live snapshotting": EngineStates.RUNNING,
#      "unknown": EngineStates.UNKNOWN,
#      "inaccessible": EngineStates.INEXISTENT,
#      "inexistent": EngineStates.INEXISTENT
#    }
#    state = mapping.get(vboxState, EngineStates.UNKNOWN)
#    logging.debug("Machine state: %s : %s", vboxState, state)
#    return state

  def vboxManager(self, cmd, params):
    '''
    Invoke the VirtualBoxManager
    '''
    return Shell.procCommand("%s %s %s" % (self.VBOXMAN, cmd, params)) \
      .bind(self.onVboxCommand) \
      .catch(self.onVboxError)

  def onVboxCommand(self, sh):
    return OK(sh.get('stdout', ''))

  def onVboxError(self, err):
    if isinstance(err, ShellCommandError):
      codeMatch = re.search(r'error: Details: code (VBOX_[A-Z_0-9]*)', err.stderr, re.M)
      if codeMatch:
        code = codeMatch.group(1)
      return Fail(VirtualBoxError(message=err.stderr, code=code))

    #ret = Shell.procCommand("%s %s %s" % (self.VBOXMAN, cmd, params))
    #if ret.get('returnCode'):
    #  code = None
    #  codeMatch = re.search(r'error: Details: code (VBOX_[A-Z_0-9]*)', ret.get('stderr'), re.M)
    #  if codeMatch:
    #    code = codeMatch.group(1)
    #  raise VirtualBoxError(message=ret.get('stderr'), code=code)
    #return ret

