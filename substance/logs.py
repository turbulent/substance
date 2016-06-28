import sys
import logging
import logging.config
from substance.monads import *

class StdoutFilter(logging.Filter):
  def __init__(self, level):
    self._level = level
    logging.Filter.__init__(self)

  def filter(self, rec):
    return rec.levelno < self._level

class EngineLogAdapter(logging.LoggerAdapter):
  def process(self, msg, kwargs):
    return "[%s] ==> %s" % (self.extra['name'], msg), kwargs

class DriverLogAdapter(logging.LoggerAdapter):
  def process(self, msg, kwargs):
    return "%s" % (msg), kwargs
 
class LevelLogFormatter(logging.Formatter):
  def format(self, record):
    if record.levelno == logging.DEBUG:
      record.msg = '[%s] %s' % (record.levelname, record.msg)
    return super(LevelLogFormatter , self).format(record)

LOG_SETTINGS = {
  'version': 1,
  'disable_existing_loggers': False, 
  'root': {
    'level': 'NOTSET',
  },
  'loggers': {
    'substance': {
      'level': 'NOTSET',
      'qualname': 'substance',
      'handlers': ['stdout', 'stderr'],
      'propagate': False
    },
    'subwatch': {
      'level': 'INFO',
      'qualname': 'subwatch',
      'handlers': ['console'],
      'propagate': False
    },
    'watchdog': {
      'level': 'CRITICAL',
      'handlers': ['console'],
      'propagate': False
    },
    'paramiko': {
      'level': 'CRITICAL',
      'handlers': ['console'],
      'propagate': False
    },
    'requests': {
      'level': 'CRITICAL',
      'handlers': ['console'],
      'propagate': False
    }
  },
  'handlers': {
    'console': {
      'level': 'NOTSET',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stdout',
    },
    'stdout': {
      'level': 'INFO',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stdout',
      'filters': ['StdoutFilter'],
    },
    'stderr': {
      'level': 'WARNING',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stderr'
    }
  },
  'filters': {
    'StdoutFilter': {
      '()': StdoutFilter,
      'level': logging.WARNING
    }
  },
  'formatters': {
    'levelformatter': { 
      '()': LevelLogFormatter, 'format': '%(message)s' },
    'stdout': { 'format': '%(message)s' },
    'stderr': { 'format': '%(message)s' }
  }
}

logging.config.dictConfig(LOG_SETTINGS)

logger = logging.getLogger('substance')

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
    logger.log(level, msg)
    return OK(None)
  return deferredLog

