import os
import time
import platform
import logging
import Queue
import fnmatch
from collections import OrderedDict

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.exceptions import (SubstanceError)
from substance.utils import pathComponents, getSupportFile
from substance.constants import Syncher
from substance.syncher import BaseSyncher

from subwatch.watcher import (LocalWatchAgent, RemoteWatchAgent)
from subwatch.events import WatchEventHandler
from subwatch.events import (WatchEvent, EVENT_TYPE_MODIFIED)

from tornado import ioloop

logger = logging.getLogger(__name__)

class SubwatchSyncher(BaseSyncher):

  PARTIAL_DIR = '.~subsync~'
  def __init__(self, engine, keyfile):
    super(SubwatchSyncher, self).__init__(engine, keyfile)
    self.localAgent = LocalWatchAgent(self.processLocalEvent)
    self.remoteAgent = RemoteWatchAgent(self.processRemoteEvent)
    self.synching = {Syncher.UP:{}, Syncher.DOWN:{}}
    self.toSync = {Syncher.UP:{}, Syncher.DOWN:{}}
    self.syncPeriod = 0.3 
    self.schedule = {Syncher.UP: False, Syncher.DOWN: False}
    self.excludes = []
    
  def getFolders(self):
    return reduce(lambda acc, x: acc + [x] if x.mode == 'rsync' else acc, self.engine.getEngineFolders(), [])

  def getFolderFromPath(self, path, direction=None):
    direction = Syncher.UP if not direction else direction

    for folder in self.getFolders():
      if direction is Syncher.UP and folder.hostPath == path:
        return OK(folder)
      elif direction is Syncher.DOWN and folder.guestPath == path:
        return OK(folder)
    return Fail(NameError("%s is not a folder." % path))

  def start(self, direction=Syncher.BOTH):
    op = self.ensureKeyPerms() \
      .then(defer(self.initialSync, direction=direction))
    if op.isFail():
      return op
    
    folders = self.getFolders()

    if len(folders) == 0:
      return Fail(SubstanceError("No rsync folders definedfor synchronization in engine configuration."))

    logger.info("Starting substance syncher (%s)" % direction)

    for folder in folders:
      if direction in [Syncher.UP, Syncher.BOTH]:
        self.localAgent.startWatching(folder.hostPath)
      if direction in [Syncher.DOWN, Syncher.BOTH]:
        self.remoteAgent.startWatching(folder.guestPath)

    self.remoteAgent.connect("ws://%s:%s" % (self.engine.getPublicIP(), 1500))

    try:
      self.remoteAgent.start()
      ioloop.IOLoop.current().start()
      return OK(None)
    except KeyboardInterrupt:
      return self.stop()
    except Exception as err:
      logger.error(err)
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
    #logger.info("LOCAL %s" % event)
    return self.expungeSynching(Syncher.UP).then(defer(self.processEvent, event, Syncher.UP))

  def processRemoteEvent(self, event):
    #logger.info("REMOTE %s" % event)
    return self.expungeSynching(Syncher.DOWN).then(defer(self.processEvent, event, Syncher.DOWN))

  def expungeSynching(self, direction):
    dirs = self.synching[direction]
    for dir in dirs.keys():
      t = self.synching[direction][dir]
      if (time.time() - t) > 0:
        logger.debug("Expiring ignore of (%s)%s" % (direction, dir))
        del self.synching[direction][dir]
    return OK(None)

  def ignoreSync(self, direction, folder, paths=[], timeout=1):
    for path in paths:
      logger.debug("Ignoring (%s)%s for %ss" % (direction, path, timeout))
      self.synching[direction][path] = time.time() + timeout

  def processEvent(self, event, direction=None):
    direction = Syncher.UP if direction is None else direction
  
    path = event.getRelativePath()
    folder = self.getFolderFromPath(event.watchPath, direction)
 
    if folder.isFail():
      logger.error("%s" % folder)
      return folder
    else:
      folder = folder.getOK()

    if event.type == EVENT_TYPE_MODIFIED and event.isDirectory:
      return

    if self.fileMatch(path, self.getExcludes()):
      logger.info("Ignored (excluded) event (%s)%s" % (direction, path))
      return

    if os.path.dirname(path) in self.synching[direction]:
      logger.debug("Ignored (synching) event of (%s)%s" % (direction, path))
      return

    if folder not in self.toSync[direction]:
      self.toSync[direction][folder] = []
    
    if not event.isDirectory: 
      path = os.path.dirname(path)
   
    if path not in self.toSync[direction][folder]:
      if path not in self.synching[direction]:
        self.ignoreSync(self.inverse(direction), folder, [path])
      self.toSync[direction][folder].append(path)
      self.scheduleSync(direction)

  def inverse(self, direction): 
    if direction == Syncher.UP:
      return Syncher.DOWN
    else:
      return Syncher.UP

  def fileMatch(self, filename, excludes=[]):
    for ex in excludes:
      if fnmatch.fnmatch(filename, ex):
        return True
    return False
 
  def initialSync(self, direction):
    folders = self.getFolders()
    chain = OK(None)
    for folder in folders:
      if direction in [Syncher.UP, Syncher.BOTH]:
        chain = chain.then(defer(self.syncFolder, folder=folder, direction=Syncher.UP, paths=['/'])) 
      if direction in [Syncher.DOWN, Syncher.BOTH]: 
        chain = chain.then(defer(self.syncFolder, folder=folder, direction=Syncher.DOWN, paths=['/']))
    return chain

  def incrementalSync(self, direction):
    folders = self.toSync[direction].copy()
    seq = [ self.syncFolder(folder, direction, folders[folder], incremental=True) for folder in folders ]
    self.schedule[direction] = False
    return Try.sequence(seq)

  def syncFolder(self, folder, direction, paths, incremental=False):
    filters = "\n".join(self.makeFilters(folder, paths))

    if paths:
      logger.info("Synchronizing %s %s %s:%s" % (folder.hostPath, direction, self.engine.name, folder.guestPath))

    self.toSync[direction].pop(folder, None)

    syncher = Rsync()
    syncher.setTransport(self.engine.getSSHPort(), self.keyfile)
    syncher.setFilters(self.makeFilters(folder, paths))
    #syncher.setLongOption('delay-updates', True)
    syncher.setLongOption('inplace', True)
    syncher.setLongOption('temp-dir', '/tmp')
    #syncher.setLongOption('partial-dir', self.PARTIAL_DIR)
    syncher.setLongOption('itemize-changes', True)
    syncher.setLongOption('log-format', '%o\t%n %L')

    if incremental is True:
      syncher.setLongOption('delete', True)

    if direction == Syncher.UP:
      syncher.setFrom(folder.hostPath)
      syncher.setTo(folder.guestPath, self.engine.getSSHIP(), "substance")
    elif direction == Syncher.DOWN:
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
    plus.append('*.*.ssh')
    plus.append('*.*.bash_history')
    plus.append('*.*.profile')
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
      'p':True,
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
    transport = "ssh -p %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" % self.port
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
