from .memtable import Memtable, deleted
from .wal import writeEntry, readWAL
from .sstable import writeSSTable, getSSTable

class Store:
    def __init__(self, walFilename):
        self.walFilename = walFilename
        self.table = Memtable()
        self.sstables = []
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
        tableVal = self.table.get(key)
        if tableVal is not None:
            return tableVal if tableVal != deleted else None
        else:
            for sstable in reversed(self.sstables):
                sstableVal = getSSTable(sstable, key)
                if sstableVal is not None:
                    return sstableVal if sstableVal != deleted else None
        return None


    def delete(self, key):
        writeEntry(1, key, "", self.walFilename)
        self.table.delete(key)

    def flush(self, sstFilename):
        writeSSTable(self.table, sstFilename)
        self.sstables.append(sstFilename)
        self.table = Memtable()
        with open(self.walFilename, "wb") as f:
            pass