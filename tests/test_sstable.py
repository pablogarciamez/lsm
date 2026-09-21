from lsm import Memtable, writeSSTable, getSSTable, readIndex, deleted

def test_writeSSTable_example(tmp_path):
    path = tmp_path / "table.sst"
    table = Memtable()
    table.put("a", "3")
    table.delete("b")
    table.put("carro", "xy")

    writeSSTable(table, path)

    data = path.read_bytes()
    assert len(data) == 88
    assert data == (
        # datos
        b'\x00' + b'\x01\x00\x00\x00' + b'a' + b'\x01\x00\x00\x00' + b'3'          # put a=3
        + b'\x01' + b'\x01\x00\x00\x00' + b'b' + b'\x00\x00\x00\x00'              # delete b
        + b'\x00' + b'\x05\x00\x00\x00' + b'carro' + b'\x02\x00\x00\x00' + b'xy'  # put carro=xy
        + b'\x01\x00\x00\x00' + b'a' + b'\x00\x00\x00\x00\x00\x00\x00\x00'
        + b'\x01\x00\x00\x00' + b'b' + b'\x0b\x00\x00\x00\x00\x00\x00\x00'
        + b'\x05\x00\x00\x00' + b'carro' + b'\x15\x00\x00\x00\x00\x00\x00\x00'
        + b'\x25\x00\x00\x00\x00\x00\x00\x00'
    )

def test_readIndex_example(tmp_path):
    path = tmp_path / "table.sst"
    table = Memtable()
    table.put("a", "3")
    table.delete("b")
    table.put("carro", "xy")
    writeSSTable(table, path)

    assert readIndex(path) == [("a", 0), ("b", 11), ("carro", 21)]

def test_getSSTable_example(tmp_path):
    path = tmp_path / "table.sst"
    table = Memtable()
    table.put("a", "3")
    table.delete("b")
    table.put("carro", "xy")
    writeSSTable(table, path)

    assert getSSTable(path, "a") == "3"
    assert getSSTable(path, "carro") == "xy"
    assert getSSTable(path, "b") is deleted
    assert getSSTable(path, "0") is None      # menor que todas
    assert getSSTable(path, "c") is None      # entre b y carro
    assert getSSTable(path, "zzz") is None    # mayor que todas