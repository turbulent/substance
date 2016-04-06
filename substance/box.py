import os
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.exceptions import *
import requests

class Box(object):
 
  def __init__(self, name, version, namespace, registry=None, boxstring=None):
    self.name = name
    self.version = version
    self.namespace = namespace
    self.registry = registry

  def getRegistryURL(self):
    return "http://%(registry)s/box/%(namespace)s/%(name)s-%(version)s.json" % self.__dict__

  def getArchiveURL(self):
    return "http://%(registry)s/box/%(namespace)s/%(name)s-%(version)s.box" % self.__dict__

  def getDescriptor(self):
    return {'name':self.name, 'registry':self.registry, 'namespace': self.namespace}

  def getPath(self):
    parts = [self.registry, self.namespace]
    return os.path.join(*parts)

  def getArchiveFilename(self):
    return "%(name)s-%(version)s.box" % self.__dict__

  def getArchivePath(self):
    return os.path.join(self.getPath(), self.getArchiveFilename())

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

