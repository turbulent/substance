
from platform import (system, uname)
from functools import lru_cache

@lru_cache(maxsize=None)
def isCygwin():
    return system().startswith("CYGWIN")

@lru_cache(maxsize=None)
def isWSL():
    return "microsoft" in uname()[3].lower()

@lru_cache(maxsize=None)
def isWithinWindowsSubsystem():
    return (isCygwin() or isWSL())