import logging

from substance.monads import *
from substance.logs import *
from substance.constants import Tables
from tinydb import (
    TinyDB,
    Query,
    where
)

logger = logging.getLogger(__name__)

class DB(object):

    def __init__(self, dbFile):
        self.dbFile = dbFile

    def initialize(self):
        db = Try.attempt(lambda: TinyDB(self.dbFile))
        if db.isFail():
            return db
        self.db = db.getOK()
        return OK(self)

    # -- Box methods

    def updateBoxRecord(self, box, record):
        return self.getBoxRecord(box) \
            .bind(self._updateBoxRecord, record=record)

    def removeBoxRecord(self, box):
        logger.debug("Removing box record: %s" % (box))
        return self.getBoxRecord(box).bind(lambda r: self.remove(Tables.BOXES, eids=[r.eid]) if r else OK(None))

    def _updateBoxRecord(self, element, record):
        if element:
            logger.debug("Updating box record: %s : %s" % (element, record))
            return self.update(Tables.BOXES, record, eids=[element.eid])
        else:
            logger.info("Inserting box record: %s : %s" % (element, record))
            return self.insert(Tables.BOXES, record)

    def getBoxRecord(self, box):
        q = Query()
        q = (q.name == box.name) & (q.version == box.version) & (
            q.namespace == box.namespace)
        ret = self.get(Tables.BOXES, q)
        return ret

    def getBoxRecords(self):
        return self.all(Tables.BOXES)

    # -- DB mapping

    def tables(self):
        return Try.attempt(lambda: self.db.tables())

    def purge_tables(self):
        return Try.attempt(lambda: self.db.purge_tables())

    def all(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('all', *args, **kwargs)

    def search(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('search', *args, **kwargs)

    def get(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('get', *args, **kwargs)

    def remove(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('remove', *args, **kwargs)

    def contains(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('contains', *args, **kwargs)

    def update(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('update', *args, **kwargs)

    def insert(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('insert', *args, **kwargs)

    def insert_multiple(self, table, *args, **kwargs):
        return self.readTable(table) >> self.proxyTableCommand('insert_multiple', *args, **kwargs)

    def proxyTableCommand(self, command, *args, **kwargs):
        def proxy(table):
            f = getattr(table, command)
            return Try.attempt(lambda: f(*args, **kwargs))
        return proxy

    def readTable(self, table):
        return OK(self.db.table(table))
