import sys
import yaml
import requests
import tempfile
import shutil
import logging
import collections
import functools
import os
import errno
import hashlib
import tarfile
from math import floor
from time import time
from pkg_resources import Requirement, resource_filename, require
from substance.exceptions import (
    ConfigSyntaxError,
    FileSystemError,
    FileDoesNotExist
)

logger = logging.getLogger(__name__)

_yaml_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def _dict_representer(dumper, data):
    return dumper.represent_dict(iter(data.items()))


def _dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))


yaml.add_representer(collections.OrderedDict, _dict_representer)
yaml.add_constructor(_yaml_mapping_tag, _dict_constructor)


def writeToFile(filename, the_bytes):
    try:
        with open(filename, "wb") as fh:
            fh.write(the_bytes)
    except Exception as err:
        raise FileSystemError("Failed to write to %s : %s" % (filename, err))


def writeYAML(filename, data):
    try:
        with open(filename, "w") as fileh:
            fileh.write(yaml.dump(data, default_flow_style=False))
    except Exception as err:
        raise FileSystemError("Failed to write to %s : %s" % (filename, err))


def readYAML(filename):
    try:
        with open(filename, "r") as stream:
            contents = yaml.load(stream)
            return contents
    except yaml.YAMLError as exc:
        msg = "Syntax error in file %s"
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            msg += " Error position: (%s:%s)" % (mark.line +
                                                 1, mark.column + 1)
        raise ConfigSyntaxError(msg)
    except Exception as err:
        raise FileSystemError(
            "Failed to read configuration file %s : %s" % (filename, err))


def getSupportFile(filename):
    return resource_filename(Requirement.parse('substance'), filename)


def getPackageVersion():
    return require('substance')[0].version


def readSupportFile(filename):
    try:
        keyfile = getSupportFile(filename)
        with open(keyfile, "r") as fileh:
            keydata = fileh.read()
            return keydata
    except IOError as err:
        raise FileDoesNotExist("File not found: %s" % keyfile)
    except Exception as err:
        raise FileSystemError("Failed to read: %s" % keyfile)


def streamDownload(url, destination):
    basename = os.path.basename(destination)

    try:
        with open(destination, 'wb') as fd:
            r = requests.get(url, stream=True, timeout=5)
            r.raise_for_status()
            contentLength = int(r.headers.get('content-length'))

            if contentLength is None:
                fd.write(r.content)
            else:
                progress = 0
                startTime = time()
                chunkSize = floor(contentLength / 100)
                for chunk in r.iter_content(chunk_size=chunkSize):
                    if chunk:
                        progress += len(chunk)
                        fd.write(chunk)
                        done = int(50 * progress / contentLength)
                        elapsed = (time() - startTime)
                        speed = humanReadableBytes(progress / elapsed)
                        left = humanReadableBytes(contentLength - progress)
                        sys.stdout.write(
                            "\r%s [%s%s] %s/s %s left" % (basename,  '=' * done, ' ' * (50 - done), speed, left))
                        sys.stdout.flush()
                sys.stdout.write("\n")
            fd.flush()
    except (Exception, KeyboardInterrupt) as err:
        if os.path.exists(destination):
            os.remove(destination)
        raise(err)
    return destination


def humanReadableBytes(num):
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def sha1sum(filename):
    sha = hashlib.sha1()
    bufsize = 65536
    with open(filename, 'rb') as fd:
        while True:
            data = fd.read(bufsize)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()


def makeHttpRequest(url, params=None):
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.content


def makeXHRRequest(url, params=None):
    r = requests.get(url, params=params)
    r.raise_for_status()
    payload = r.json()
    return payload


def untar(filename, destination=None):
    tar = tarfile.open(filename)
    tar.extractall(destination)
    tar.close()
    return filename


def mergeDict(a, b, path=None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                mergeDict(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


# merge 2 dicts and overwrite target keys with source keys if collision
def mergeDictOverwrite(target, source):
    merged = target.copy()
    merged.update(source)
    return merged


def readDotEnv(filepath, env={}):
    with open(filepath) as f:
        return parseDotEnv(f, env)


def parseDotEnv(dotenvdata, env={}):
    for line in dotenvdata:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        v = v.strip("'").strip('"')
        env[k] = v
    return env


def makeSymlink(source, link, force=False):
    try:
        os.symlink(source, link)
    except OSError as e:
        if e.errno == errno.EEXIST and force:
            os.remove(link)
            os.symlink(source, link)
        else:
            raise e


def readSymlink(link):
    return os.readlink(link)


def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


class CommandList(list):
    def commands(self):
        cmds = list(filter(lambda x: x is not None, self))
        return flatten(cmds)

    def joined(self, by=' '):
        return by.join(self.commands())

    def logicAnd(self):
        return self.joined(' && ')

    def logicOr(self):
        return self.joined(' || ')


class Memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


class DictCompat(dict):
    def iteritems():
        return self.items()
