import time
import statistics
import tempfile
from pathlib import Path
from lsm import Memtable, Store

REPETICIONES = 5
TAMANOS = [1000, 2000, 4000, 8000]

for n in TAMANOS:
    tiempos = []
    for r in range(REPETICIONES):
        memtable = Memtable()
        claves = []
        valores = []
        for i in range(n):
            claves.append(f"key{i:06d}")
            valores.append(f"val{i:06d}")

        inicio = time.perf_counter()

        for i in range(n):
            memtable.put(claves[i], valores[i])

        fin = time.perf_counter()

        tiempos.append(fin - inicio)

    mediana = statistics.median(tiempos)
    print(f"memtable_put  n={n:5d}  {mediana*1000:9.2f} ms  {mediana/n*1e6:7.2f} us/op")

for n in TAMANOS:
    tiempos = []
    for r in range(REPETICIONES):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "data.wal", maxLength= n + 1)
            claves = []
            valores = []
            for i in range(n):
                claves.append(f"key{i:06d}")
                valores.append(f"val{i:06d}")

            inicio = time.perf_counter()

            for i in range(n):
                store.put(claves[i], valores[i])

            fin = time.perf_counter()

            tiempos.append(fin - inicio)

    mediana = statistics.median(tiempos)
    print(f"store_put  n={n:5d}  {mediana*1000:9.2f} ms  {mediana/n*1e6:7.2f} us/op")

for n in TAMANOS:
    tiempos = []
    for r in range(REPETICIONES):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "data.wal", maxLength= n // 4)
            claves = []
            for i in range(n):
                claves.append(f"key{i:06d}")
                store.put(f"key{i:06d}", f"val{i:06d}")
            store.compact()

            inicio = time.perf_counter()

            for i in range(n):
                store.get(claves[(i * 7919) % n])

            fin = time.perf_counter()

            tiempos.append(fin - inicio)

    mediana = statistics.median(tiempos)
    print(f"get  n={n:5d}  {mediana*1000:9.2f} ms  {mediana/n*1e6:7.2f} us/op")

for n in TAMANOS:
    tiempos = []
    for r in range(REPETICIONES):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "data.wal", maxLength=n // 4)
            for i in range(n):
                store.put(f"key{i:06d}", f"val{i:06d}")

            inicio = time.perf_counter()

            store.compact()

            fin = time.perf_counter()

            tiempos.append(fin - inicio)

    mediana = statistics.median(tiempos)
    print(f"compact  n={n:5d}  {mediana*1000:9.2f} ms  {mediana/n*1e6:7.2f} us/op")

for n in TAMANOS:
    tiempos = []
    for r in range(REPETICIONES):
        with tempfile.TemporaryDirectory() as d:
            store = Store(Path(d) / "data.wal", maxLength= n + 1)
            for i in range(n):
                store.put(f"key{i:06d}", f"val{i:06d}")

            inicio = time.perf_counter()

            otherStore = Store(Path(d) / "data.wal", maxLength= n + 1)

            fin = time.perf_counter()

            tiempos.append(fin - inicio)

    mediana = statistics.median(tiempos)
    print(f"recovery  n={n:5d}  {mediana*1000:9.2f} ms  {mediana/n*1e6:7.2f} us/op")

