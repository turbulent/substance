import yaml
import collections
from pkg_resources import Requirement, resource_filename

from substance.exceptions import (
  ConfigSyntaxError,
  FileSystemError,
  FileDoesNotExist
)

_yaml_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def _dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())

def _dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, _dict_representer)
yaml.add_constructor(_yaml_mapping_tag, _dict_constructor)

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


def readSupportFile(filename):
  try:
    keyfile = resource_filename(Requirement.parse("substance"), filename)
    with open(keyfile, "r") as fileh:
      keydata = fileh.read()
      return keydata
  except IOError as err:
    raise FileDoesNotExist("File not found: %s" % keyfile)
  except Exception as err:
    raise FileSystemError("Failed to read: %s" % keyfile)
