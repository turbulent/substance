import logging
from substance.monads import *

def debug(msg, *args, **kwargs):
  return log(logging.DEBUG, msg, *args, **kwargs)

def info(msg, *args, **kwargs):
  return log(logging.INFO, msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
  return log(logging.WARNING, msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
  return log(logging.CRITICAL, msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
  return log(logging.EXCEPTION, msg, *args, **kwargs)

def log(level, msg, *args, **kwargs):
  return defer(logging.log, level, msg, *args, **kwargs)

