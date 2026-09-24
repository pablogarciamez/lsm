from lsm import Store, readIndex, getSSTable, deleted

def test_store_without_existing_wal(tmp_path):
    path = tmp_path / "data.wal"
    store = Store(path)

    assert store.get("a") is None

    store.put("a", "1")
    assert store.get("a") == "1"


def test_store_with_existing_wal(tmp_path):
    path = tmp_path / "data.wal"

    first = Store(path)
    first.put("a", "1")
    first.put("b", "2")
    first.delete("b")

    second = Store(path)

    assert second.get("a") == "1"
    assert second.get("b") is None

def test_truncated_delete_keeps_previous_value(tmp_path):
    path = tmp_path / "data.wal"
    store = Store(path)
    store.put("a", "1")
    size_before = len(path.read_bytes())
    store.delete("a")
    data = path.read_bytes()

    for cut in range(size_before, len(data)):
        path.write_bytes(data[:cut])
        assert Store(path).get("a") == "1", f"fails when cutting at byte {cut}"


def test_complete_delete_survives_restart(tmp_path):
    path = tmp_path / "data.wal"
    store = Store(path)
    store.put("a", "1")
    store.delete("a")

    assert Store(path).get("a") is None


def test_truncated_put_keeps_previous_value(tmp_path):
    path = tmp_path / "data.wal"
    store = Store(path)
    store.put("a", "1")
    size_before = len(path.read_bytes())
    store.put("a", "2")
    data = path.read_bytes()

    for cut in range(size_before, len(data)):
        path.write_bytes(data[:cut])
        assert Store(path).get("a") == "1", f"fails when cutting at byte {cut}"


def test_truncated_put_of_new_key_leaves_others_intact(tmp_path):
    path = tmp_path / "data.wal"
    store = Store(path)
    store.put("a", "1")
    store.put("b", "2")
    size_before = len(path.read_bytes())
    store.put("ñandú", "€uro")
    data = path.read_bytes()

    for cut in range(size_before, len(data)):
        path.write_bytes(data[:cut])
        restarted = Store(path)
        assert restarted.get("ñandú") is None, f"fails when cutting at byte {cut}"
        assert restarted.get("a") == "1", f"fails when cutting at byte {cut}"
        assert restarted.get("b") == "2", f"fails when cutting at byte {cut}"

def test_flush(tmp_path):
    wal = tmp_path / "data.wal"
    sst = tmp_path / "table.sst"
    store = Store(wal)
    store.put("a", "1")
    store.put("b", "3")
    store.put("c", "5")
    store.put("d", "6")
    store.delete("b")
    store.flush(sst)
    assert sst.exists()
    assert [k for k, pos in readIndex(sst)] == ["a", "b", "c", "d"]
    assert getSSTable(sst, "a") == "1"
    assert getSSTable(sst, "b") is deleted
    assert store.table.data == []
