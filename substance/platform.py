
from platform import (system, uname)
from substance.utils import Memoized

@Memoized
def isCygwin():
    return system().startswith("CYGWIN")

@Memoized
def isWSL():
    return "microsoft" in uname()[3].lower()

@Memoized
def isWithinWindowsSubsystem():
    return (isCygwin() or isWSL())