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

def test_compact_store(tmp_path):
    sst_dir = tmp_path / "ssts"
    wal_dir = tmp_path / "data.wal"
    sst_dir.mkdir()
    store = Store(wal_dir, directory = sst_dir, maxLength = 2)
    store.put("a", "1")
    store.put("b", "2")
    store.put("c", "3")
    store.delete("a")
    store.put("b", "4")
    store.put("d", "1")
    store.compact()
    assert len(store.sstables) == 1
    assert len(list(sst_dir.glob("*.sst"))) == 1
    assert list(sst_dir.glob("*.sst"))[0].stem == "3"
    assert store.get("a") is None
    assert store.get("b") == "4"


def test_kill_mid_write_no_corruption(tmp_path):
    sst_dir = tmp_path / "ssts"
    wal_dir = tmp_path / "data.wal"
    sst_dir.mkdir()

    # Un flush legítimo previo, hecho de forma normal (sin matar nada)
    store = Store(wal_dir, directory = sst_dir, maxLength = 2)
    store.put("old", "safe")
    store.put("old2", "safe2")
    assert (sst_dir / "0.sst").exists()

    # Simulamos el SIGUIENTE flush (1.sst) muriendo a mitad de la escritura.
    # El worker escribe deliberadamente despacio (ver _kill_worker.py) y
    # avisa con un archivo "marker" justo al empezar, para no depender de
    # lo rápido o lento que vaya el disco de la máquina que ejecute esto.
    import subprocess, sys, time
    from pathlib import Path
    worker = Path(__file__).parent / "_kill_worker.py"
    target = sst_dir / "1.sst"
    marker = tmp_path / "started.marker"

    proc = subprocess.Popen(
        [sys.executable, str(worker), str(target), str(marker), "30", "0.05"]
    )
    deadline = time.time() + 5
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.001)
    assert marker.exists(), "el worker nunca llegó a avisar; el test no prueba nada"
    proc.kill()
    proc.wait()

    # El archivo final NUNCA debió llegar a existir: el rename no se ejecutó
    assert not target.exists()
    # Y el flush anterior, ya válido en disco, no se ha tocado
    assert (sst_dir / "0.sst").exists()

    # Recrear el Store sobre el mismo directorio no debe fallar ni perder nada
    store2 = Store(wal_dir, directory = sst_dir, maxLength = 2)
    assert [p.name for p in store2.sstables] == ["0.sst"]
    assert store2.get("old") == "safe"
    assert store2.get("old2") == "safe2"