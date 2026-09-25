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
    store = Store(wal)
    store.put("a", "1")
    store.put("b", "3")
    store.put("c", "5")
    store.put("d", "6")
    store.delete("b")
    store.flush()

    sst = store.sstables[-1]
    assert sst.exists()
    assert sst.parent == tmp_path
    assert [k for k, pos in readIndex(sst)] == ["a", "b", "c", "d"]
    assert getSSTable(sst, "a") == "1"
    assert getSSTable(sst, "b") is deleted
    assert store.table.data == []
    assert wal.read_bytes() == b""

def test_get_from_sstable(tmp_path):
    wal = tmp_path / "data.wal"
    store = Store(wal)
    store.put("a", "1")
    store.put("b", "3")
    store.flush()
    store.delete("a")
    assert store.get("b") == "3"
    assert store.get("a") is None

def test_overwrite_after_flush(tmp_path):
    store = Store(tmp_path / "data.wal")
    store.put("a", "1")
    store.flush()
    store.put("a", "2")

    assert store.get("a") == "2"


def test_newer_sstable_wins(tmp_path):
    store = Store(tmp_path / "data.wal")
    store.put("a", "1")
    store.flush()
    store.put("a", "2")
    store.flush()

    assert store.get("a") == "2"


def test_delete_in_sstable_hides_older_value(tmp_path):
    store = Store(tmp_path / "data.wal")
    store.put("a", "1")
    store.flush()
    store.delete("a")
    store.flush()

    assert store.get("a") is None


def test_get_unknown_key_returns_none(tmp_path):
    store = Store(tmp_path / "data.wal")
    store.put("a", "1")
    store.flush()

    assert store.get("z") is None

def test_put_triggers_flush_at_limit(tmp_path):
    store = Store(tmp_path / "data.wal", maxLength=3)
    store.put("a", "1")
    store.put("b", "2")
    assert store.sstables == []

    store.put("c", "3")

    assert len(store.sstables) == 1
    assert store.table.data == []
    assert (tmp_path / "data.wal").read_bytes() == b""
    assert store.get("a") == "1"
    assert store.get("b") == "2"
    assert store.get("c") == "3"


def test_many_puts_create_distinct_sstables(tmp_path):
    store = Store(tmp_path / "data.wal", maxLength=3)
    for i in range(10):
        store.put(f"k{i}", str(i))

    assert len(store.sstables) == 3
    assert len(set(store.sstables)) == 3
    assert all(p.exists() for p in store.sstables)
    for i in range(10):
        assert store.get(f"k{i}") == str(i)


def test_overwrite_across_automatic_flushes(tmp_path):
    store = Store(tmp_path / "data.wal", maxLength=2)
    store.put("a", "1")
    store.put("b", "1")   # flush 1: a=1, b=1
    store.put("a", "2")
    store.put("c", "1")   # flush 2: a=2, c=1

    assert len(store.sstables) == 2
    assert store.get("a") == "2"
    assert store.get("b") == "1"


def test_delete_can_trigger_flush_and_hides_old_value(tmp_path):
    store = Store(tmp_path / "data.wal", maxLength=2)
    store.put("a", "1")
    store.put("b", "1")   # flush 1
    store.delete("a")
    store.delete("b")     # flush 2: dos borrados

    assert len(store.sstables) == 2
    assert store.get("a") is None
    assert store.get("b") is None

def test_sstables_go_in_given_directory(tmp_path):
    sst_dir = tmp_path / "ssts"
    sst_dir.mkdir()
    store = Store(tmp_path / "data.wal", directory=sst_dir, maxLength=1)
    store.put("a", "1")

    assert store.sstables[0].parent == sst_dir

def test_recreate_store(tmp_path):
    sst_dir = tmp_path / "ssts"
    wal_dir = tmp_path / "data.wal"
    sst_dir.mkdir()
    store1 = Store(wal_dir, directory = sst_dir, maxLength = 1)
    store1.put("a", "2")
    store1.put("b", "5")
    store1.delete("a")
    store2 = Store(wal_dir, directory = sst_dir, maxLength = 1)
    store2.put("b", "6")
    assert int(store2.sstables[-1].stem) == 3
    assert store2.get("a") is None
    assert store2.get("b") == "6"