import re
from substance.logs import *
from substance.monads import *
from substance.driver import Driver
from substance.shell import Shell
from substance.constants import (EngineStates)
from substance.exceptions import (
  SubstanceDriverError,
  ShellCommandError,
  VirtualBoxError, 
  VirtualBoxMissingAdditions
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
    '''
    Inspect an OVF file to extract it's examined output
    '''

    return self.vboxManager("import", "-n %s" % ovfFile) 
    
  def makeImportParams(self, inspection, name, engineProfile=None):
    '''
    Make the import parameter commands based on name, engine profile and inspection
    '''

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
    '''
    Import the OVF file as a virtual box vm.
    '''

    importParams.insert(0, ovfFile)
    return self.vboxManager("import", " ".join(importParams)) \
      .then(defer(self.getMachineID, name))

  def deleteMachine(self, uuid):
    '''
    Delete the machine by driver identifier.
    '''
    return self.vboxManager("unregistervm", "--delete \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

  def startMachine(self, uuid):
    '''
    Start the machine by driver identifier.
    '''
    return self.vboxManager("startvm", "--type headless \"%s\"" % (uuid)) \
      .bind(lambda x: OK(uuid))

  def suspendMachine(self, uuid):
    '''
    Suspend the machine.
    '''
    return self.vboxManager("controlvm", "\"%s\" savestate" % uuid) \
      .bind(lambda x: OK(uuid))

  def haltMachine(self, uuid):
    '''
    Halt the machine.
    '''
    return self.vboxManager("controlvm", "\"%s\" acpipowerbutton" % uuid) \
      .bind(lambda x: OK(uuid))
    
  def terminateMachine(self, uuid):
    '''
    Terminate the machine forcefully.
    '''
    return self.vboxManager("controlvm", "\"%s\" poweroff" % uuid) \
      .bind(lambda x: OK(uuid))

  def getMachineInfo(self, uuid):
    '''
    Retrieve the machine info from the driver.
    '''
    return self.vboxManager("showvminfo", "--machinereadable \"%s\"" % uuid) \
      .bind(self.parseMachineInfo)

  def getMachines(self):
    '''
    Retrive the list of machines and their driver identifiers.
    '''
    self.vboxManager("list", "vms") >> self.parseMachinesList

  def parseMachinesList(self, vms):
    '''
    Parse the output of "list vms" and return a dict of machine name to machine id.
    '''
    matcher = re.compile(r'"([^"]+)" {([^}]+)}')
    machines = {}
    for line in vms.split("\n"):
      parts = matcher.match(line)
      if parts:
        machines[parts.group(1)] = parts.group(2)
    return OK(machines)

  def parseMachinesForID(self, vms, uuid):
    '''
    Parse the output of list vms to find if uuid exists.
    '''
    if re.search(r'"([^"]+)" {'+re.escape(uuid)+'}', vms, re.M):
      return OK(True)
    else:
      return OK(False)

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

  def fetchGuestProperty(self, uuid, prop):
    return self.vboxManager("guestproperty", "get %s %s" % (uuid, prop)) \
      .bind(self.parseGuestProperty)

  def parseGuestProperty(self, prop): 
    prop = prop.strip()

    if prop == 'No value set!' or not prop:
      return OK(None)

    match = re.match(r'^Value: (.+?)$', prop)
    if match:
      return OK(match.group(1))
    else:
      return Fail(VirtualBoxError(None, "Failed to to parse guest property output : %s" % prop))
   
  def fetchGuestAddVersion(self, uuid):
    return self.fetchGuestProperty(uuid, "/VirtualBox/GuestAdd/Version") \
      .bind(self.parseGuestAddVersion) \
      .catchError(VirtualBoxMissingAdditions, lambda x: self.fetchGuestAddVersionFromInfo(uuid=uuid))

  def fetchGuestAddVersionFromInfo(self, uuid):
    def extractGuestAdd(info):
      if 'GuestAdditionsVersion' in info:
        return OK(info['GuestAdditionsVersion'])
      else:
        return OK(None)

    return self.getMachineInfo(uuid) \
      .bind(extractGuestAdd) \
      .bind(self.parseGuestAddVersion)

  def parseGuestAddVersion(self, guestAdd):
    if guestAdd is None:
      return Fail(VirtualBoxMissingAdditions("VirtualBox guest additions are not installed."))

    parts = guestAdd.split("_", 1)
    if len(parts) >= 1:
      return OK(parts[0])
    else:
      return Fail(VirtualBoxMissingAdditions("VirtualBox guest additions are not installed."))
 
  def getMachineID(self, name):
    '''
    Retrieve the driver specific machine ID for a machine name.
    '''
    return self.vboxManager("list", "vms") \
      .bind(self.parseMachinesList) \
      .bind(lambda x: OK(x[name]) if name in x else Fail("No Machine ID found for \"%s\"" %name))

  def exists(self, uuid):
    '''
    Check in the driver that the specified identifier exists.
    '''
    return self.vboxManager("list", "vms") >> defer(self.parseMachinesForID, uuid=uuid)

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
    '''
    Parse the output of showvminfo to extrcat the VM state
    '''
    if re.search(r'^name="<inaccessible>"$', vminfo, re.M):
      return OK('inaccessible')
    
    stateMatch = re.search(r'^VMState="(.+?)"$', vminfo, re.M)
    if stateMatch:
      return OK(stateMatch.group(1))
    else:
      return OK('inexistent')
  
  def getMachineState(self, uuid):
    '''
    Retrieve the Substance machine state for this driver id
    '''
    return self.getInternalState(uuid) >> self.vboxStateToMachineState

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
      code = codeMatch.group(1) if codeMatch else None
      return Fail(VirtualBoxError(message=err.stderr, code=code))
