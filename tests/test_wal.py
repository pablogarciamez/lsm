from lsm import writeEntry, readEntry, readWAL

def test_writeEntry():
    with open("test.wal", "wb") as f:
        pass
    writeEntry(0, "a", "3", "test.wal")
    writeEntry(1, "a", "", "test.wal")

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
            assert len(entries) == 0, f"fails when cutting at byte {cut}"
        else:
            assert len(entries) == 1, f"fails when cutting at byte {cut}"