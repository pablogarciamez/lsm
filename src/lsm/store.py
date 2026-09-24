from .memtable import Memtable
from .wal import writeEntry, readWAL
from .sstable import writeSSTable

class Store:
    def __init__(self, walFilename):
        self.walFilename = walFilename
        self.table = Memtable()
        try:
            entries = readWAL(walFilename)
        except FileNotFoundError:
            entries = []

        for entry in entries:
            if entry[0] == 0:
                self.table.put(entry[1], entry[2])
            else:
                self.table.delete(entry[1])

    def put(self, key, val):
        writeEntry(0, key, val, self.walFilename)
        self.table.put(key, val)

    def get(self, key):
        return self.table.get(key)

    def delete(self, key):
        writeEntry(1, key, "", self.walFilename)
        self.table.delete(key)

    def flush(self, sstFilename):
        writeSSTable(self.table, sstFilename)
        self.table = Memtable()
        with open(self.walFilename, "wb") as f:
            pass