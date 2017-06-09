import os

from substance.monads import OK

class BaseSyncher(object):
  def __init__(self, engine, keyfile):
    self.keyfile = keyfile
    self.engine = engine

  def ensureKeyPerms(self):
    try:
      # XXX Hack for perms on insecure file. Temporary until distribution is sorted out.
      os.chmod(self.keyfile, 0600)
    except Exception as err:
      pass 
    return OK(None)
 