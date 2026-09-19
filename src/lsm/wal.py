def writeEntry(type, key, val, filename = 'data.wal'):
    encodedKey = key.encode('utf-8')
    encodedVal = val.encode('utf-8')
    with open(filename, 'ab') as f:
        f.write(type.to_bytes(1, 'little'))
        f.write(len(encodedKey).to_bytes(4, 'little'))
        f.write(encodedKey)
        f.write(len(encodedVal).to_bytes(4, 'little'))
        f.write(encodedVal)

def readEntry(f):
    typeBytes = f.read(1)
    if typeBytes == b'':
        return None
    type = int.from_bytes(typeBytes, 'little')
    lenKeyBytes = f.read(4)
    if len(lenKeyBytes) != 4:
            return None
    lenKey = int.from_bytes(lenKeyBytes, 'little')
    try:
        key = f.read(lenKey).decode('utf-8')
    except UnicodeDecodeError:
        return None
    if len(key.encode('utf-8')) != lenKey:
        return None
    lenValBytes = f.read(4)
    if len(lenValBytes) != 4:
        return None
    lenVal = int.from_bytes(lenValBytes, 'little')
    try:
        val = f.read(lenVal).decode('utf-8')
    except UnicodeDecodeError:
        return None
    if len(val.encode('utf-8')) != lenVal:
        return None
    return type, key, val

def readWAL(fileName):
    entries = []
    with open(fileName, 'rb') as f:
        entry = readEntry(f)
        while entry != None:
            entries.append(entry)
            entry = readEntry(f)
        return entries