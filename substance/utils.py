import sys
import yaml
import requests
import tempfile
import shutil
import logging
import collections
import os, errno
import hashlib
import tarfile
from time import time
from pkg_resources import Requirement, resource_filename, require
from substance.exceptions import (
  ConfigSyntaxError,
  FileSystemError,
  FileDoesNotExist
)

logger = logging.getLogger(__name__)

_yaml_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def _dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())

def _dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, _dict_representer)
yaml.add_constructor(_yaml_mapping_tag, _dict_constructor)

def writeToFile(filename, data):
  try:
    with open(filename, "wb") as fh:
      fh.write(data)
  except Exception as err:
    raise FileSystemError("Failed to write to %s : %s" % (filename, err))
 
def writeYAML(filename, data):
  try:
    with open(filename, "w") as fileh:
      fileh.write(yaml.dump(data, default_flow_style=False))
  except Exception as err:
    raise FileSystemError("Failed to write to %s : %s" % (filename, err))

def readYAML(filename):
  try:
    stream = open(filename, "r")
    contents = yaml.load(stream)
    return contents
  except yaml.YAMLError, exc:
    msg = "Syntax error in file %s"
    if hasattr(exc, 'problem_mark'):
      mark = exc.problem_mark
      msg += " Error position: (%s:%s)" % (mark.line+1, mark.column+1)
    raise ConfigSyntaxError(msg)
  except Exception as err:
    raise FileSystemError("Failed to read configuration file %s : %s" % (filename, err))

def getSupportFile(filename):
  return resource_filename(Requirement.parse('substance'), filename)
 
def getPackageVersion():
  return require('substance')[0].version

def readSupportFile(filename):
  try:
    keyfile = getSupportFile(filename)
    with open(keyfile, "r") as fileh:
      keydata = fileh.read()
      return keydata
  except IOError as err:
    raise FileDoesNotExist("File not found: %s" % keyfile)
  except Exception as err:
    raise FileSystemError("Failed to read: %s" % keyfile)


def streamDownload(url, destination):
  basename = os.path.basename(destination)

  try:
    with open(destination, 'wb') as fd:
      r = requests.get(url, stream=True, timeout=1)
      r.raise_for_status()
      contentLength = int(r.headers.get('content-length'))
  
      if contentLength is None:
        fd.write(r.content)
      else:
        progress = 0
        startTime = time()
        chunkSize = contentLength/100
        for chunk in r.iter_content(chunk_size=chunkSize):
          if chunk:
            progress += len(chunk)
            fd.write(chunk)
            done = int(50 * progress / contentLength)
            elapsed = (time() - startTime)
            speed = humanReadableBytes(progress / elapsed)
            left = humanReadableBytes(contentLength - progress)
            sys.stdout.write("\r%s [%s%s] %s/s %s left" % (basename,  '=' * done, ' ' * (50-done), speed, left) )
            sys.stdout.flush()
        sys.stdout.write("\n")
      fd.flush()
  except (Exception, KeyboardInterrupt) as err:
    if os.path.exists(destination):
      os.remove(destination)
    raise(err)
  return destination


def humanReadableBytes(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def sha1sum(filename):
  sha = hashlib.sha1()
  bufsize = 65536
  with open(filename, 'rb') as fd:
    while True:
      data = fd.read(bufsize)
      if not data:
        break
      sha.update(data)
  return sha.hexdigest()

def makeHttpRequest(url, params=None):
  r = requests.get(url, params=params)
  r.raise_for_status()
  return r.content

def makeXHRRequest(url, params=None):
  r = requests.get(url, params=params)
  r.raise_for_status()
  payload = r.json()
  return payload

def untar(filename, destination=None):
  tar = tarfile.open(filename)
  tar.extractall(destination)
  tar.close()
  return filename

def pathComponents(path):
  folders = []
  path = os.path.normpath(path)
  while 1:
    path, folder = os.path.split(path)
  
    if folder != "":
      folders.append(folder)
    else:
      if path != "":
        folders.append(path)
      break

  folders.reverse()  
  return folders

def mergeDict(a, b, path=None):
  if path is None: path = []
  for key in b:
    if key in a:
      if isinstance(a[key], dict) and isinstance(b[key], dict):
        mergeDict(a[key], b[key], path + [str(key)])
      elif a[key] == b[key]:
        pass # same leaf value
      else:
        a[key] = b[key]
    else:
      a[key] = b[key]
  return a

def readDotEnv(filepath, env={}):
  with open(filepath) as f:
    return parseDotEnv(f, env)

def parseDotEnv(dotenvdata, env={}):
  for line in dotenvdata:
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
      continue
    k, v = line.split('=', 1)
    v = v.strip("'").strip('"')
    env[k] = v
  return env

def makeSymlink(source, link, force=False):
  try:
    os.symlink(source, link)
  except OSError, e:
    if e.errno == errno.EEXIST and force:
      os.remove(link)
      os.symlink(source, link)
    else:
      raise e

def readSymlink(link):
  return os.readlink(link)


def expandLocalPath(path, basePath=None):
  path = os.path.expanduser(path)
  if not os.path.isabs(path) and basePath:
    path = os.path.normpath(path)
    path = os.path.join(basePath, path)
  return os.path.abspath(os.path.realpath(path))

