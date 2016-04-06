import os
import logging
import requests
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.exceptions import *
from substance.shell import Shell
from substance.utils import (
  readYAML,
  writeYAML,
  readSupportFile,
  getSupportFile,
  streamDownload,
  makeXHRRequest,
  sha1sum,
  untar
)

class Box(object):
 
  def __init__(self, core, name, version, namespace, registry=None, boxstring=None):
    self.core = core
    self.name = name
    self.version = version
    self.namespace = namespace
    self.registry = registry
    self.boxstring = boxstring

  def getRegistryURL(self):
    return "http://%(registry)s/box/%(namespace)s/%(name)s-%(version)s.json" % self.__dict__

  def getArchiveURL(self):
    return "http://%(registry)s/box/%(namespace)s/%(name)s-%(version)s.box" % self.__dict__

  def getDescriptor(self):
    return {'name':self.name, 'registry':self.registry, 'namespace': self.namespace}

  def getPath(self):
    parts = [self.core.getBoxesPath(), self.registry, self.namespace, self.name, self.version]
    return os.path.join(*parts)

  def getFilePath(self, filename):
    return os.path.join(self.getPath(), filename)

  def getArchivePath(self):
    return self.getFilePath("box.box")

  def getOVFFile(self):
    return self.getFilePath("box.ovf")

  def getImageName(self):
    return "%(name)s:%(version)s" % self.__dict__

  @staticmethod
  def fromBoxString(name):
    return Box.parseBoxString(name).map(lambda b: Box(**b))

  @staticmethod
  def parseBoxString(name):
    '''
    Parse a box string into dict of the components.

    Format: namespace/name:VERSION@registry
    registry and version are optional.
    '''

    box = OrderedDict()

    box['boxstring'] = name
    parts = name.split("@", 1)
    # turbulent/substance-box:0.1@public-registry
    boxstring = parts[0]

    if len(parts) > 1:
      box['registry'] = parts[1]
    else:
      box['registry'] = "bbeausej.developers.turbulent.ca"

    # XXX Configure this default from core?

    parts = boxstring.split("/", 1)
    if len(parts) <= 1:
      return Fail(InvalidBoxName("Name \"%s\" does not reference a valid box name: Missing namespace." % name))

    (box['namespace'], imagestring) = parts
    # substance-box:0.1

    imageparts = imagestring.split(":", 1)
    if len(imageparts) > 1:
      (box['name'], box['version']) = imageparts
    else:
      box['name'] = imageparts[0]
      box['version'] = 'latest'

    return OK(box)

  def fetch(self):
    if self.isDownloaded():
      return OK(self)

    manifestURL = self.getRegistryURL()
    return Try.attempt(makeXHRRequest, url=manifestURL) >> defer(self.download)

  def isDownloaded(self):
    return True if os.path.exists(self.getOVFFile()) else False

  def download(self, boxResult):
    archiveURL = boxResult['archiveURL']
    archiveSHA = boxResult['archiveSHA1']
    archive = self.getArchivePath()

    logging.info("Downloading %s:%s (%s)" % (self.name, self.version, boxResult['archiveURL']))

    return Try.sequence([
      Shell.makeDirectory(os.path.dirname(archive)),
      Try.attempt(streamDownload, url=archiveURL, destination=archive) \
        .then(defer(self.verifyArchive, expectedSHA=archiveSHA)) \
        .then(defer(self.unpackArchive)),
      self.core.getDB().updateBoxRecord(self, boxResult)
    ]).map(lambda x: self)

  def verifyArchive(self, expectedSHA):
    logging.info("Verifying archive for %s" % self.getImageName())
    archive = self.getArchivePath()
    sha = sha1sum(archive)
    if sha == expectedSHA:
      return OK(self)
    else:
      Try.attempt(lambda: os.remove(archive))
      return Fail(BoxArchiveHashMismatch("Box archive hash mismatch. Failed download?"))

  def unpackArchive(self):
    return Try.sequence([ 
      Try.attempt(untar, self.getArchivePath(), self.getPath()),
      Shell.rmFile(self.getArchivePath())
    ])
