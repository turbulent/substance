from substance import (Command, Engine)
from substance.constants import Syncher


class Sync(Command):
    def getShellOptions(self, optparser):
        optparser.add_option(
            "-u", "--up", dest="up", help="Synchronize UP to the engine only.", default=False, action="store_true")
        optparser.add_option("-d", "--down", dest="down",
                             help="Synchronize DOWN from the engine only.", default=False, action="store_true")
        optparser.add_option(
            "-i",
            "--ignore-archives",
            dest="ignorearchives",
            help="Ignore previous Unison archives and rebuild them (unison sync mode only)",
            default=False,
            action="store_true")
        return optparser

    def getUsage(self):
        return "substance sync [options] [SUBPATH]"

    def getHelpTitle(self):
        return "Synchronize & watch the devroot of the current engine"

    def getHelpDetails(self):
        return """
This process will run in the foreground and monitor local and remote file
system events to perform bidirectional file synchronization. When working
locally ; activate the sync command to keep your code up to date on the engine
or to receive artifact stored in the devroot in your local folders.

By default, this command syncs the entire engine home directory. You can
optionally pass a sub-path to the sync command. The sub-path is relative from
the current engine's home directory. If a valid sub-path is specified, then
syncing will only be active from within that sub-path, but the sub-path MUST
be valid on both sides of the sync (it will never be automatically created for
you).
"""

    def main(self):

        if self.getOption('up'):
            direction = Syncher.UP
        elif self.getOption('down'):
            direction = Syncher.DOWN
        else:
            direction = Syncher.BOTH

        path = ""
        if self.args:
            path = self.args[0]

        return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
            .bind(Engine.loadConfigFile) \
            .bind(self.syncFolders, direction=direction, path=path) \
            .catch(self.exitError)

    def syncFolders(self, engine, direction=Syncher.BOTH, path=''):
        syncher = engine.getSyncher()
        if self.getOption('ignorearchives'):
            syncher.ignoreArchives = True
        return syncher.start(direction, path)
