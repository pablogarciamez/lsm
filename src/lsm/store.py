from .memtable import Memtable, deleted
from .wal import writeEntry, readWAL
from .sstable import writeSSTable, getSSTable, mergeSSTables
from pathlib import Path

class Store:
    def __init__(self, walFilename, directory = None, maxLength = 100):
        self.walFilename = walFilename
        self.table = Memtable()
        if directory is None:
            directory = Path(walFilename).parent
        self.directory = Path(directory)
        self.sstables = sorted(self.directory.glob("*.sst"), key = lambda p: int(p.stem))
        self.counter = 0 if self.sstables == [] else int(self.sstables[-1].stem) + 1
        self.maxLength = maxLength
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
        if len(self.table.data) >= self.maxLength:
            self.flush()

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
        if len(self.table.data) >= self.maxLength:
            self.flush()

    def flush(self):
        sstFilename = self.directory / f"{self.counter}.sst"
        writeSSTable(self.table, sstFilename)
        self.counter += 1
        self.sstables.append(sstFilename)
        self.table = Memtable()
        with open(self.walFilename, "wb") as f:
            pass

    def compact(self):
        sstFilename = self.directory / f"{self.counter}.sst"
        writeSSTable(mergeSSTables(sorted(self.directory.glob("*.sst"), key = lambda p: int(p.stem))),sstFilename)
        self.counter += 1
        self.sstables.append(sstFilename)
        for path in self.sstables[:-1]:
            path.unlink()
        self.sstables = [self.sstables[-1]]