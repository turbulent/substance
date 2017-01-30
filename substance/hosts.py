import logging
import tempfile
import os
from python_hosts import Hosts, HostsEntry
from shutil import copyfile
from substance.monads import *
from substance.shell import Shell

logger = logging.getLogger(__name__)

class SubHosts(Hosts):

  def __init__(self, path=None, tempFile=None):
    super(SubHosts, self).__init__(path)
    self.tempFile = tempFile

  def addEntry(self, name, destAddress):
    self.removeEntry(name)
    entry = HostsEntry(entry_type='ipv4', address=destAddress, names=[name])
    self.add([entry], True)
    return entry

  def removeEntry(self, name):
    self.remove_all_matching(None, name)

  @staticmethod
  def register(name, destAddress):
    try:
      logger.info("Hosts register %s: %s" % (name, destAddress))
      hosts = SubHosts.checkoutFromSystem()
      entry = hosts.findEntryByAddress(address=destAddress)
      if entry is None:
        logger.info("'%s' Not found in local hosts file. Adding." % destAddress)
        entry = hosts.addEntry(name, destAddress)
        hosts.write()
        hosts.commitToSystem()

      if name not in entry.names:
        logger.info("'%s' Not found in local hosts file. Adding." % name)
        existing = hosts.findEntryByName(name=name)
        if existing:
          existing.names.remove(name)
        entry.names.append(name)
        hosts.write()
        hosts.commitToSystem()
      else:
        logger.info("'%s' found in local hosts file." % name)
 
      return OK(None)
    except Exception as err:
      return Fail(err)

  @staticmethod
  def unregister(name):
    try:
      logger.info("Hosts unregister %s" % (name))
      hosts = SubHosts.checkoutFromSystem()
      if hosts.exists(names=[name]):
        hosts.removeEntry(name)
        hosts.write()
        hosts.commitToSystem()
      return OK(None)
    except Exception as err:
      return Fail(err)
  
  @staticmethod
  def checkoutFromSystem():
    tempFile = tempfile.NamedTemporaryFile(delete=False)
    tempFile.close()
    hostsPath = Hosts.determine_hosts_path()
    logger.debug("Checking out '%s' from system to '%s'" % (hostsPath, tempFile.name))
    copyfile(hostsPath, tempFile.name)
    return SubHosts(tempFile.name, tempFile)

  def commitToSystem(self):
    hostsPath = self.determine_hosts_path()
    logger.debug("Commiting '%s' to system '%s'" % (self.hosts_path, hostsPath))
    return Shell.call(["cp", self.hosts_path, self.determine_hosts_path()], shell=False, sudo=True) \
      .then(lambda: os.remove(self.tempFile.name))

  def findEntryByAddress(self, address):
    for entry in self.entries:
      entry_names = entry.names if entry.names is not None else []
      if address and address == entry.address:
        return entry
    return None

  def findEntryByName(self, name):
    for entry in self.entries:
      entry_names = entry.names if entry.names is not None else []
      if name in entry_names:
        return entry
    return None
 
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

