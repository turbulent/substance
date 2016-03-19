import logging
from substance.monads import *

def ddebug(msg, *args, **kwargs):
  return dlog(logging.DEBUG, msg, *args, **kwargs)

def dinfo(msg, *args, **kwargs):
  return dlog(logging.INFO, msg, *args, **kwargs)

def dwarning(msg, *args, **kwargs):
  return dlog(logging.WARNING, msg, *args, **kwargs)

def dcritical(msg, *args, **kwargs):
  return dlog(logging.CRITICAL, msg, *args, **kwargs)

def dexception(msg, *args, **kwargs):
  return dlog(logging.EXCEPTION, msg, *args, **kwargs)

def dlog(level, msg, *args, **kwargs):
  if args:
    msg = msg % args
  def deferredLog(*args, **kwargs):
    logging.log(level, msg)
    return OK(True)
  return deferredLog
