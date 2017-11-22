from substance import (Engine, Command)
from substance.exceptions import (LinkCommandError)


class Run(Command):

    def getUsage(self):
        return "substance run JOBCONTAINER [ARGS...]"

    def getHelpTitle(self):
        return "Run a job container with arguments"

    def getShellOptions(self, optparser):
        return optparser

    # Disable parsing for this command
    def execute(self, args=None):
        self.input = args
        self.args = args

        self.main()

    def main(self):

        if len(self.args) == 0:
            return self.exitError("Please provide a jobcontainer name to run.")
        
        task = self.args[0]
        args = self.args[1:]

        return self.core.loadCurrentEngine(name=self.parent.getOption('engine')) \
            .bind(Engine.loadConfigFile) \
            .bind(Engine.envRun, task=task, args=args) \
            .catch(self.onEngineException)

    def onEngineException(self, err):
        return self.exitError(err)
