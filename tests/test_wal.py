
from lsm import writeEntry, readEntry, readWAL

def test_writeEntry(tmp_path):
    path = tmp_path / "wal.log"
    writeEntry(0, "a", "3", path)
    writeEntry(1, "a", "", path)
    assert path.read_bytes() == (
        b'\x00' + b'\x01\x00\x00\x00' + b'a' + b'\x01\x00\x00\x00' + b'3'   # put a=3
        + b'\x01' + b'\x01\x00\x00\x00' + b'a' + b'\x00\x00\x00\x00' + b''  # delete a
    )

def test_readEntry():
    with open("test.wal", "wb") as f:
            pass
    writeEntry(0, "a", "3", "test.wal")
    writeEntry(1, "a", "", "test.wal")
    with open("test.wal", "rb") as f:
        assert readEntry(f) == (0, "a", "3")

def test_readWAL():
    with open("test.wal", "wb") as f:
        pass
    writeEntry(0, "a", "3", "test.wal")
    writeEntry(1, "a", "", "test.wal")
    assert readWAL("test.wal") == [(0, "a", "3"), (1, "a", "")]

def test_truncate_at_every_byte(tmp_path):
    path = tmp_path / "wal.log"

    writeEntry(1, "a", "1", path)
    first_size = len(path.read_bytes())

    writeEntry(1, "ñandú", "€uro", path)
    data = path.read_bytes()

    for cut in range(len(data)):
        path.write_bytes(data[:cut])
        entries = readWAL(path)

        if cut < first_size:
            assert entries == [], f"fails when cutting at byte {cut}"
        else:
            assert entries == [(1, "a", "1")], f"fails when cutting at byte {cut}"