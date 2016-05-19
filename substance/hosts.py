import tempfile
from python_hosts import Hosts, HostsEntry
from shutil import copyfile
from substance.monads import *
from substance.shell import Shell

class SubHosts(Hosts):

  def __init__(self, path=None, tempFile=None):
    super(SubHosts, self).__init__(path)
    self.tempFile = tempFile

  def addEngine(self, engine):
    self.removeEngine(engine)
    entry = HostsEntry(entry_type='ipv4', address=engine.getPublicIP(), names=[engine.name])
    self.add([entry])

  def removeEngine(self, engine):
    self.remove_all_matching(None, engine.name)

  @staticmethod
  def checkoutFromSystem():
    tempFile = tempfile.NamedTemporaryFile()
    hostsPath = Hosts.determine_hosts_path()
    copyfile(hostsPath, tempFile.name)
    return SubHosts(tempFile.name, tempFile)

  def commitToSystem(self):
    return Shell.command("sudo cp \"%s\" \"%s\"" % (self.hosts_path, self.determine_hosts_path())) \
      .then(lambda: self.tempFile.close())

  def exists(self, address=None, names=[]):
    for entry in self.entries:
      entry_names = entry.names if entry.names is not None else []
      if address and address == entry.address:
        return True
      if len(names) > 0:
        for name in names:
          if name in entry_names:
            return True
    return False

