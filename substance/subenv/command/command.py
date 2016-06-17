from substance import Command

class SubenvCommand(Command):

  def __init__(self, core=None, api=None):
    super(SubenvCommand, self).__init__(core)
    self.api = api
