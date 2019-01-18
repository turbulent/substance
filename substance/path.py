import sys
import platform
import os
import re
from substance.shell import (Shell)
from subprocess import check_output
from substance.utils import Memoized
from pathlib import (PureWindowsPath, PurePosixPath)

from substance.platform import (isWSL, isCygwin)


@Memoized
def inner(path):
    if isCygwin():
        path = check_output(["cygpath", "-u", path]).decode().strip()
    if isWSL() and PureWindowsPath(path).drive:
        path = check_output(["wslpath", "-u", path]).decode().strip()
    return path


@Memoized
def outer(posixPath):
    if isCygwin():
        path = check_output(["cygpath", "-w", posixPath]).decode().strip()
    elif isWSL():
        path = check_output(["wslpath", "-w", posixPath]).decode().strip()
    else:
        path = posixPath
    return path


@Memoized
def getHomeDirectory(subpath=None):
    if isWSL():
        homePath = getWindowsHomeDirectory()
    else:
        homePath = getUnixHomeDirectory()

    path = homePath.joinpath(subpath) if subpath else homePath
    return inner(str(path))


@Memoized
def getUnixHomeDirectory():
    return PurePosixPath(os.path.expanduser('~'))


@Memoized
def getWindowsHomeDirectory():
    winPath = PureWindowsPath(check_output(["cmd.exe", "/C", 'echo %USERPROFILE%']).decode().strip())
    return PurePosixPath(winPath.as_posix())


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


def expandLocalPath(path, basePath=None):
    path = os.path.expanduser(path)
    if not os.path.isabs(path) and basePath:
        path = os.path.normpath(path)
        path = os.path.join(basePath, path)
    return os.path.abspath(os.path.realpath(path))
