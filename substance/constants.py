
from builtins import object
class Constants(object):

  class ConstError(TypeError):
    pass

  def __init__(self, **kwargs):
    for name, value in list(kwargs.items()):
      super(Constants, self).__setattr__(name, value)

  def __setattr__(self, name, value):
    if name in self.__dict__:
      raise self.ConstError("Can't rebind const(%s)"%name)
    self.__dict__[name] = value

  def __delattr__(self, name):
    if name in self.__dict__:
      raise self.ConstError("Can't unbind const(%s)"%name)
    raise NameError(name)

Tables = Constants(
  BOXES="boxes"
)

EngineStates = Constants(
  RUNNING="running",
  STOPPED="stopped",
  SUSPENDED="suspended",
  UNKNOWN="unknown",
  INEXISTENT="inexistent"
)

Syncher = Constants(
  UP=">>",
  DOWN="<<",
  BOTH="<>"
)

