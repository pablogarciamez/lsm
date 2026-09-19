from lsm import Memtable

def test_put_and_read():
    m = Memtable()
    m.put("a", "1")
    m.put("x", "3")
    m.put("l", "Hola")
    assert m.get("l") == "Hola"

def test_read_deleted():
    m = Memtable()
    m.put("a", "3")
    m.put("c", "3")
    m.delete("c")
    assert m.get("c") == None

def test_read_not_put():
    m = Memtable()
    assert m.get("a") == None

def test_double_put():
    m = Memtable()
    m.put("a", "3")
    m.put("a", "4")
    assert m.get("a") == "4"

def test_large_memtable_get():
    m = Memtable()
    m.put("a", "3")
    m.put("b", "3")
    m.put("c", "3")
    m.put("d", "3")
    m.put("e", "3")
    m.put("f", "3")
    m.put("g", "3")
    m.put("h", "3")
    assert m.get("e") == "3"

def test_delete_not_put():
    m = Memtable()
    m.put("a", "3")
    m.put("c", "3")
    m.delete("b")
    assert m.get("b") == None

def test_delete_empty():
    m = Memtable()
    m.delete("b")
    assert m.get("b") == None

