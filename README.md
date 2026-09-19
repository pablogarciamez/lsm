# lsm

An LSM-tree key-value store written from scratch in Python, following the design used by storage engines such as LevelDB and RocksDB.

Status: in development. Currently implemented:

- In-memory memtable with put, get and delete
- Write-ahead log (WAL): every write is logged before being applied, and the store rebuilds its state from the log on startup
- Crash recovery tested by truncating the WAL at every possible byte, including mid-character in multi-byte UTF-8 keys

Not yet implemented: SSTables, compaction.

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