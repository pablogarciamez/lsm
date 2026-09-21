from .memtable import Memtable, deleted
from .wal import readEntry

def writeSSTable(memtable, path):
    index = []
    with open(path, 'wb') as f:
        for keyVal in memtable.data:
            index.append([keyVal[0], f.tell()])
            type = 1 if keyVal[1] == deleted else 0
            encodedKey = keyVal[0].encode('utf-8')
            f.write(type.to_bytes(1, 'little'))
            f.write(len(encodedKey).to_bytes(4, 'little'))
            f.write(encodedKey)
            val = "" if keyVal[1] == deleted else keyVal[1]
            encodedVal = val.encode('utf-8')
            f.write(len(encodedVal).to_bytes(4, 'little'))
            f.write(encodedVal)
        indexStart = f.tell()
        for keyPos in index:
            encodedKey = keyPos[0].encode('utf-8')
            f.write(len(encodedKey).to_bytes(4, 'little'))
            f.write(encodedKey)
            f.write(keyPos[1].to_bytes(8, 'little'))
        f.write(indexStart.to_bytes(8, 'little'))

def readIndex(path):
    index = []
    with open(path, 'rb') as f:
        f.seek(-8, 2)
        indexEnd = f.tell()
        indexStart = int.from_bytes(f.read(8), 'little')
        f.seek(indexStart, 0)
        while f.tell() < indexEnd:
            lenKey = int.from_bytes(f.read(4), 'little')
            key = f.read(lenKey).decode('utf-8')
            pos = int.from_bytes(f.read(8), 'little')
            index.append((key, pos))
    return index

def getSSTable(path, key):
    index = readIndex(path)
    low, high = 0, len(index) - 1
    while(low <= high):
        mid = (low + high) // 2
        if index[mid][0] == key:
            with open(path, 'rb') as f:
                f.seek(index[mid][1])
                entry = readEntry(f)
                return deleted if entry[0] == 1 else entry[2]
        if index[mid][0] < key: low = mid + 1
        else: high = mid - 1
    return None

