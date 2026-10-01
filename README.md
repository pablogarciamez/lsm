# lsm

An LSM-tree key-value store written from scratch in Python, following the design used by storage engines such as LevelDB and RocksDB.

Status: complete as a learning implementation (34 tests passing). Implemented:

- **Memtable**: in-memory sorted table with `put`, `get` and `delete` (deletes are stored as tombstones).
- **Write-ahead log (WAL)**: every write is logged before being applied, and the store rebuilds its state from the log on startup.
- **SSTables**: immutable on-disk files (data, index and footer), written to a temporary file and renamed into place, so a half-written file never appears under its final name. Lookups use a binary search over the index. The byte format is documented in [SSTABLE.md](SSTABLE.md).
- **Flush and reads**: when the memtable reaches `maxLength` entries (default 100) it is flushed to a new SSTable and the WAL is reset. Reads check the memtable first, then the SSTables from newest to oldest, and a tombstone hides any older value.
- **Compaction**: `Store.compact()` merges all SSTables into one, keeping the latest value of each key and dropping tombstones.
- **Restart**: a new `Store` on the same directory rediscovers the existing SSTables and replays the WAL.
- **Crash recovery, tested**: the WAL is truncated at every possible byte (including mid-character in multi-byte UTF-8 keys), and a test kills a process (SIGKILL) in the middle of writing an SSTable and checks that the unfinished file never appears, that earlier data is untouched, and that a new `Store` starts and reads it correctly.

Known limitations:

- No checksums: corruption in the middle of a file is not detected.
- Durability is tested against process kills, not power loss: nothing calls `fsync`.
- The whole SSTable index is loaded into memory on every read.
- Compaction is total (no levels) and must be called manually.
- Memtable insertion is a linear scan over a sorted list, O(n) per `put`.
- The SSTable directory must already exist.

A Rust port of this store is in [lsm-rust](https://github.com/pablogarciamez/lsm-rust).

## Installation

```bash
git clone https://github.com/pablogarciamez/lsm
cd lsm
pip install -e .
```

## Usage

```python
from lsm import Store

store = Store("data.wal")
store.put("a", "3")
store.put("b", "4")
store.delete("a")

print(store.get("a"))  # None
print(store.get("b"))  # 4

restarted = Store("data.wal")
print(restarted.get("b"))  # 4
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```