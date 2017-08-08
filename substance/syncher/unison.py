import os
import logging
import platform

from substance.utils import pathComponents, getSupportFile
from substance.constants import Syncher
from substance.shell import Shell
from substance.syncher import BaseSyncher
from substance.monads import Try
from substance.link import Link

logger = logging.getLogger(__name__)


class UnisonSyncher(BaseSyncher):

    def __init__(self, engine, keyfile):
        super(UnisonSyncher, self).__init__(engine, keyfile)
        self.ignoreArchives = False

    def start(self, direction, path=''):
        self.ensureKeyPerms()
        unisonPath = self.getUnisonBin()
        unisonArgs = self.getUnisonArgs(direction, path)
        unisonEnv = self.getUnisonEnv()
        if self.ignoreArchives:
            # It seems that in certain cases, unison does not observe the -ignorearchives flag correctly
            # So to make sure, we forcibly delete previous archives on both sides
            res = Try.sequence([
                # Delete host archives
                Shell.call(["rm", "-rf", unisonEnv['UNISON']], shell=False),
                # Delete guest archives
                self.engine.readLink().bind(Link.runCommand, 'rm -rf /substance/.unison')
            ])
            if res.isFail():
                return res
        logger.info("Syncing local directory %s to remote directory %s", unisonArgs[-2], unisonArgs[-1])
        logger.debug("EXEC: %s", Shell.stringify([unisonPath] + unisonArgs, unisonEnv))
        os.execve(unisonPath, unisonArgs, unisonEnv)

    def getUnisonBin(self):
        unisonDir = self.getUnisonSupportDirectory()
        logger.debug("Dir: %s", unisonDir)
        return os.path.join(unisonDir, 'unison')

    def getUnisonArgs(self, direction, path=''):
        folder = self.engine.getEngineFolders()[0]
        localRoot = Shell.normalizePath(os.path.join(folder.hostPath, path))
        remoteRoot = 'ssh://substance@%s/%s/%s' % (
            self.engine.getSSHIP(), folder.guestPath.rstrip('/'), path.lstrip('/'))

        # Direction arguments
        if direction == Syncher.UP:
            directionArgs = ['-nocreation', localRoot,
                             '-nodeletion', localRoot, '-noupdate', localRoot]
        elif direction == Syncher.DOWN:
            directionArgs = ['-nocreation', remoteRoot,
                             '-nodeletion', remoteRoot, '-noupdate', remoteRoot]
        else:
            directionArgs = ['-prefer', 'newer', '-copyonconflict']

        # User args
        userArgs = folder.syncArgs

        # Other arguments
        rootArgs = [localRoot, remoteRoot]
        ignoreArgs = [item for sublist in [['-ignore', 'Name ' + excl]
                                           for excl in folder.excludes] for item in sublist]

        # SSH config
        transport = "-p %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" % self.engine.getSSHPort()
        if self.keyfile is not None:
            transport += " -i %s" % Shell.normalizePath(self.keyfile)

        # Assemble everything
        args = ['-batch', '-repeat', 'watch', '-sshargs', transport] + \
            userArgs + directionArgs + ignoreArgs + rootArgs
        if self.ignoreArchives and '-ignorearchives' not in args:
            args.insert(0, '-ignorearchives')
        return args

    def getUnisonEnv(self):
        # Add the unison-fsmonitor binary to PATH
        path = self.getUnisonSupportDirectory() + os.pathsep + os.environ.get('PATH', '')
        # Tell unison to save all replica state to ~/.substance/unison
        unisonDir = Shell.normalizePath(os.path.join(
            self.engine.core.getBasePath(), 'unison'))
        homeDir = os.environ.get('HOME', os.path.expanduser('~'))
        return {'UNISON': unisonDir, 'PATH': path, 'HOME': homeDir, 'SSH_AUTH_SOCK': os.environ.get('SSH_AUTH_SOCK', '')}

    def getUnisonSupportDirectory(self):
        osTarget = None
        osName = os.name
        psys = platform.system()
        if osName == 'posix':
            if "CYGWIN" in psys:
                osTarget = 'windows'
            elif "Darwin" in psys:
                osTarget = 'macos-10.12'
            elif "Linux" in psys:
                osTarget = 'ubuntu-14.04'
            else:
                raise NotImplementedException()
        elif osName == 'nt' and "Windows" in psys:
            osTarget = 'windows'
        else:
            raise NotImplementedException()
        return getSupportFile(os.path.join('support', 'unison', osTarget))
