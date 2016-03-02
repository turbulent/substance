import yaml
from substance.exceptions import (
  ConfigSyntaxError,
  FileSystemError
)

def readYAML(filename):
  try:
    stream = open(filename, "r")
    contents = yaml.load(stream)
  except yaml.YAMLError, exc:
    msg = "Syntax error in file %s"
    if hasattr(exc, 'problem_mark'):
      mark = exc.problem_mark
      msg += " Error position: (%s:%s)" % (mark.line+1, mark.column+1)
    raise ConfigSyntaxError(msg)
  except Exception as err:
    raise FileSystemError("Failed to read configuration file %s : %s" % (filename, err))
  return contents
