import os
import time
import logging
import Queue

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.exceptions import (SubstanceError)

from subwatch.watcher import (LocalWatchAgent, RemoteWatchAgent)
from subwatch.events import WatchEventHandler
from subwatch.events import WatchEvent

from tornado import ioloop

logging.getLogger("watchdog").setLevel(logging.CRITICAL)

class SubstanceSyncher(object):

  UP = "up"
  DOWN = "down"

  def __init__(self, engine, keyfile):
    self.keyfile = keyfile
    self.engine = engine
    self.localAgent = LocalWatchAgent(self.processLocalEvent)
    self.remoteAgent = RemoteWatchAgent(self.processRemoteEvent)
    self.unison = {}
    self.synching = {}
    self.toSync = {self.UP:{}, self.DOWN:{}}
    self.syncPeriod = 0.4
    self.schedule = {self.UP: False, self.DOWN: False}

  def getFolders(self):
    return self.engine.getEngineFolders()

  def getFolderFromHostPath(self, path):
    for folder in self.getFolders():
      if folder.hostPath == path:
        return OK(folder)
    return Fail(NameError("%s is not a folder." % path))

  def getFolderFromGuestPath(self, path):
    for folder in self.getFolders():
      if folder.guestPath == path:
        return OK(folder)
    return Fail(NameError("%s is not a folder." % path))
   
  def start(self):
    op = self.initialSync()
    if op.isFail():
      return op
    
    folders = self.getFolders()
    for folder in folders:
      self.localAgent.startWatching(folder.hostPath)

    self.remoteAgent.connect("ws://%s:%s" % (self.engine.getPublicIP(), 1500))
    self.remoteAgent.startWatching(folder.guestPath)

    try:
      self.remoteAgent.start()
      ioloop.IOLoop.current().start()
      return OK(None)
    except KeyboardInterrupt:
      return self.stop()
    except Exception as err:
      logging.error(err)
      return Fail(err)
    finally:
      return self.stop()

    return OK(None)

  def stop(self):
    self.localAgent.stop()
    self.remoteAgent.stop()
    ioloop.IOLoop.current().stop()
    return OK(None)
 
  def processLocalEvent(self, event):
    logging.info("LOCAL %s" % event)
    folder = self.getFolderFromHostPath(event.watchPath)
    if folder.isFail():
      return folder
    else:
      folder = folder.getOK()

    if folder not in self.toSync[self.UP]:
      self.toSync[self.UP][folder] = []
    
    path = event.getRelativePath()
    if not event.isDirectory: 
      path = os.path.dirname(path)

    if path not in self.toSync[self.UP][folder]:
      self.toSync[self.UP][folder].append(path)
      self.scheduleSyncUp()
  
  def scheduleSyncUp(self):
    if self.schedule[self.UP] is False:
      self.schedule[self.UP] = True
      ioloop.IOLoop.current().call_later(self.syncPeriod, defer(self.incrementalSync, direction=self.UP))
 
  def processRemoteEvent(self, event):
    logging.info("REMOTE %s" % event)


  def initialSync(self):
    folders = self.getFolders()
    chain = OK(None)
    for folder in folders:
      chain = chain.then(defer(self.syncFolder, folder=folder, direction=self.UP, paths=['/'])) \
        .then(defer(self.syncFolder, folder=folder, direction=self.DOWN, paths=['/']))
    return chain

  def incrementalSync(self, direction):
    folders = self.toSync[direction].copy()
    seq = [ self.syncFolder(folder, direction, folders[folder], incremental=True) for folder in folders ]
    self.schedule[direction] = False
    return Try.sequence(seq)

  def syncFolder(self, folder, direction, paths, incremental=False):
    filters = "\n".join(self.pathsToFilters(folder, paths))

    logging.info("Synchronizing %s %s %s:%s" % (folder.hostPath, direction, self.engine.name, folder.guestPath))
    logging.info("%s" % filters)
    self.toSync[direction].pop(folder, None)

    syncher = Rsync()
    syncher.setTransport(self.engine.getSSHPort(), self.keyfile)
    syncher.setFilters(self.pathsToFilters(folder, paths))
    syncher.setLongOption('delay-updates', True)
    syncher.setLongOption('partial-dir', '.~subsync~')

    if incremental is True:
      syncher.setLongOption('delete', True)

    if direction == self.UP:
      syncher.setFrom(folder.hostPath)
      syncher.setTo(folder.guestPath, self.engine.getSSHIP(), "substance")
    elif direction == self.DOWN:
      syncher.setFrom(folder.guestPath, self.engine.getSSHIP(), "substance")
      syncher.setTo(folder.hostPath)
    else:
      return Fail(ValueError("Sync direction must be 'up' or 'down'"))

    return syncher.sync() \
      .then(dinfo("Finished sync of %s %s %s:%s" % (folder.hostPath, direction, self.engine.name, folder.guestPath))) \
      .then(lambda: OK(folder))

  def pathsToFilters(self, folder, paths):
    filters = []
    for path in paths:
      p = ''.join(path.rsplit(os.sep, 1))
      filters.append("+ "+p+"/")
      filters.append("+ "+p+"/**")
    filters.append("- *")
    return filters

class Rsync(object):
  
  def __init__(self):
    self.fromPath = None
    self.fromHost = None
    self.fromUsername = None
    self.toPath = None
    self.toHost = None
    self.toUsername = None
  
    self.filters = []
    self.opt = {
      'm':True,
      'a':True,
      'r':True,
      'u':True
    }
    self.longopt = {}

  def setTransport(self, port=22, keyfile=None):
    self.port = port
    self.keyfile = keyfile

  def setFrom(self, path, host=None, username=None):
    self.fromPath = path
    if not self.fromPath.endswith(os.sep):
      self.fromPath += os.sep
    self.fromHost = host
    self.fromUsername = username

  def setTo(self, path, host=None, username=None):
    self.toPath = path
    if not self.toPath.endswith(os.sep):
      self.toPath += os.sep
    self.toHost = host
    self.toUsername = username

  def setFilters(self, filters):
    self.filters = filters

  def setLongOption(self, option, v):  
    if v: 
      self.longopt[option] = v
    else:
      self.longopt.pop(option, None)
 
  def setToggleOption(self, option, v):
    if len(option) > 1:
      raise ValueError("Toggle options should be single letters.")

    if v:
      self.opt[option] = v
    else:
      self.opt.pop(option, None)

  def getCommandFilters(self):
    return "\n".join(self.filters)
 
  def getCommandOpt(self):
    return ''.join(self.opt.keys())
 
  def getCommandLongOpt(self):
    opts = ""
    for k, v in self.longopt.iteritems():
      if v is True:
        opts += " --%s" % k
      elif v:
        opts += " --%s=\"%s\"" % (k,v)
    return opts 

  def getCommandFrom(self):
    dest = self.fromPath
    if self.fromHost:
      dest = self.fromHost+":"+dest
      if self.fromUsername:
        dest = self.fromUsername+"@"+dest
    return dest

  def getCommandTo(self):
    dest = self.toPath
    if self.toHost:
      dest = self.toHost+":"+dest
      if self.toUsername:
        dest = self.toUsername+"@"+dest
    return dest

  def getCommandTransport(self):
    transport = "ssh -p %s" % self.port
    if self.keyfile is not None:
      transport += " -i \"%s\"" % self.keyfile
    return transport

  def getCommand(self): 

    params = {
      'filters': self.getCommandFilters(),
      'opt': self.getCommandOpt(),
      'longopt': self.getCommandLongOpt(),
      'transport': self.getCommandTransport(),
      'from': self.getCommandFrom(),
      'to': self.getCommandTo()
    }
    return "echo '%(filters)s' | rsync -%(opt)se '%(transport)s' %(longopt)s --include-from=- %(from)s %(to)s" % params

  def sync(self):
    op = Shell.call(self.getCommand())
    if op.isFail():
      print("%s" % op)
      return op
    return OK(self)
