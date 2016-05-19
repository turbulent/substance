import os
import time
import logging
import Queue
import fnmatch
from collections import OrderedDict

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.exceptions import (SubstanceError)
from substance.utils import pathComponents

from subwatch.watcher import (LocalWatchAgent, RemoteWatchAgent)
from subwatch.events import WatchEventHandler
from subwatch.events import (WatchEvent, EVENT_TYPE_MODIFIED)

from tornado import ioloop

logging.getLogger("watchdog").setLevel(logging.CRITICAL)

class SubstanceSyncher(object):

  UP = ">>"
  DOWN = "<<"
  PARTIAL_DIR = '.~subsync~'

  def __init__(self, engine, keyfile):
    self.keyfile = keyfile
    self.engine = engine
    self.localAgent = LocalWatchAgent(self.processLocalEvent)
    self.remoteAgent = RemoteWatchAgent(self.processRemoteEvent)
    self.unison = {}
    self.synching = {}
    self.toSync = {self.UP:{}, self.DOWN:{}}
    self.syncPeriod = 0.3
    self.schedule = {self.UP: False, self.DOWN: False}
    self.excludes = []
    
  def getFolders(self):
    return reduce(lambda acc, x: acc + [x] if x.mode == 'rsync' else acc, self.engine.getEngineFolders(), [])

  def getFolderFromPath(self, path, direction=None):
    direction = self.UP if not direction else direction

    for folder in self.getFolders():
      if direction is self.UP and folder.hostPath == path:
        return OK(folder)
      elif direction is self.DOWN and folder.guestPath == path:
        return OK(folder)
    return Fail(NameError("%s is not a folder." % path))
 
  def start(self):
    op = self.initialSync()
    if op.isFail():
      return op
    
    folders = self.getFolders()

    if len(folders) == 0:
      return Fail(SubstanceError("No rsync folders definedfor synchronization in engine configuration."))

    for folder in folders:
      self.localAgent.startWatching(folder.hostPath)
      self.remoteAgent.startWatching(folder.guestPath)

    self.remoteAgent.connect("ws://%s:%s" % (self.engine.getPublicIP(), 1500))

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
  
  def scheduleSync(self, direction):
    if self.schedule[direction] is False:
      self.schedule[direction] = True
      ioloop.IOLoop.current().call_later(self.syncPeriod, defer(self.incrementalSync, direction=direction))

  def processLocalEvent(self, event):
    #logging.info("LOCAL %s" % event)
    return self.processEvent(event, self.UP)

  def processRemoteEvent(self, event):
    #logging.info("REMOTE %s" % event)
    return self.processEvent(event, self.DOWN)

  def processEvent(self, event, direction=None):
    direction = self.UP if direction is None else direction
  
    path = event.getRelativePath()
    folder = self.getFolderFromPath(event.watchPath, direction)

    if folder.isFail():
      logging.error("%s" % folder)
      return folder
    else:
      folder = folder.getOK()

    if event.type == EVENT_TYPE_MODIFIED and event.isDirectory:
      logging.debug("IGNORED")
      return

    if self.fileMatch(path, self.getExcludes()):
      logging.debug("IGNORED")
      return

    if folder not in self.toSync[direction]:
      self.toSync[direction][folder] = []
    
    if not event.isDirectory: 
      path = os.path.dirname(path)
   
    if path not in self.toSync[direction][folder]:
      self.toSync[direction][folder].append(path)
      self.scheduleSync(direction)

  def fileMatch(self, filename, excludes=[]):
    for ex in excludes:
      if fnmatch.fnmatch(filename, ex):
        return True
    return False
 
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
    filters = "\n".join(self.makeFilters(folder, paths))

    logging.info("Synchronizing %s %s %s:%s" % (folder.hostPath, direction, self.engine.name, folder.guestPath))
    self.toSync[direction].pop(folder, None)

    syncher = Rsync()
    syncher.setTransport(self.engine.getSSHPort(), self.keyfile)
    syncher.setFilters(self.makeFilters(folder, paths))
    syncher.setLongOption('delay-updates', True)
    syncher.setLongOption('partial-dir', self.PARTIAL_DIR)
    syncher.setLongOption('itemize-changes', True)
    syncher.setLongOption('log-format', '%o\t%n %L')

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

  def getExcludes(self):
    exs = self.excludes
    plus = []
    #plus.append('*.git/index.lock')
    plus.append('*.~subsync~')
    plus.append('*.~subsync~/**')
    plus.append('*.*.swo')
    plus.append('*.*.swp')
    plus.append('*.*.swpx')
    plus.append('*.DS_Store')
    return exs + plus

  def setExcludes(self, excludes=[]):
    self.excludes = excludes

  def makeFilters(self, folder, includes=[]):
    filters = []

    exs = folder.getExcludes() + self.getExcludes()
    for ex in exs:
      filters.append("- "+ex)

    inc = OrderedDict()
    for path in includes:
      p = ''
      parts = pathComponents(path)
      for part in parts:
        p = os.path.join(p, part)
        if p not in inc:
          inc[p] = os.sep
        if part == parts[-1]:
          inc[p] = os.sep+"***"

    for path, opt in inc.iteritems():
      path = ''.join(path.rsplit(os.sep, 1)) if path.endswith(os.sep) else path
      filters.append("+ "+path+opt)

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
    transport = "ssh -p %s -o StrictHostKeyChecking=no" % self.port
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
