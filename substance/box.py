from builtins import object
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

logger = logging.getLogger(__name__)

class Box(object):
 
  def __init__(self, core, name, version, namespace, registry=None, boxstring=None, archiveSHA1=None):
    self.core = core
    self.name = name
    self.version = version
    self.namespace = namespace
    self.registry = registry
    self.boxstring = boxstring
    self.archiveSHA1 = archiveSHA1

  def getRegistryURL(self):
    return "https://%(registry)s/%(namespace)s/%(name)s/%(version)s.json" % self.__dict__

  def getArchiveURL(self):
    return "https://%(registry)s/%(namespace)s/%(name)s/%(version)s.box" % self.__dict__

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
    boxstring = parts[0]

    if len(parts) > 1:
      box['registry'] = parts[1]
    else:
      box['registry'] = "dl.bintray.com/turbulent/substance-images"

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
    logger.debug("Downloading manifest: %s", manifestURL)
    return Try.attempt(makeXHRRequest, url=manifestURL) \
      .catch(lambda err: Fail(InvalidBoxName("Failed to fetch the box manifest for %s. Does this box exist?" % self.boxstring))) \
      .bind(defer(self.download))

  def isDownloaded(self):
    return True if os.path.exists(self.getOVFFile()) else False

  def getShortBoxString(self):
    return "%s/%s:%s" % (self.namespace, self.name, self.version)

  def delete(self):
    logger.info("Removing box %s from box cache", self.getShortBoxString())
    return Try.sequence([
      Shell.nukeDirectory(self.getPath()),
      self.core.getDB().removeBoxRecord(self)
    ])

  def download(self, boxResult):
    archiveURL = boxResult['archiveURL']
    archiveSHA = boxResult['archiveSHA1']
    archive = self.getArchivePath()

    logger.info("Downloading %s:%s (%s)", self.name, self.version, boxResult['archiveURL'])

    return Try.sequence([
      Shell.makeDirectory(os.path.dirname(archive)),
      Try.attempt(streamDownload, url=archiveURL, destination=archive) \
        .then(defer(self.verifyArchive, expectedSHA=archiveSHA)) \
        .then(defer(self.unpackArchive)),
      self.core.getDB().updateBoxRecord(self, boxResult)
    ]).map(lambda x: self)

  def getArchiveHash(self):
    return sha1sum(self.getArchivePath())

  def verifyArchive(self, expectedSHA):
    logger.info("Verifying archive for %s", self.getImageName())
    sha = self.getArchiveHash()
    if sha == expectedSHA:
      return OK(self)
    else:
      Try.attempt(lambda: os.remove(self.getArchivePath()))
      return Fail(BoxArchiveHashMismatch("Box archive hash mismatch. Failed download?"))

  def unpackArchive(self):
    return Try.sequence([
      Try.attempt(untar, self.getArchivePath(), self.getPath()),
      Shell.rmFile(self.getArchivePath())
    ])
