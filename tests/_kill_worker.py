"""
Proceso auxiliar para test_kill_mid_write. Se lanza como subprocess aparte
para poder matarlo de verdad (SIGKILL) mientras escribe.

Problema real que resuelve este diseño: la velocidad de escritura varía
mucho según la máquina y su carga (de menos de 50ms a más de 700ms para
300.000 claves en pruebas hechas durante el desarrollo de este test).
Vigilar la aparición de un archivo temporal desde el proceso padre es una
carrera contra un tiempo impredecible: a veces la ventana es demasiado
corta para detectarla con seguridad.

Solución: en vez de pasarle a writeSSTable una lista normal, le pasamos un
iterable (SlowData) que, al empezar a recorrerse, dos cosas:
  1. Escribe un archivo de aviso ("started.marker") justo antes de entregar
     la primera entrada.
  2. Introduce una pequeña pausa entre entrada y entrada.
writeSSTable no distingue una lista de cualquier otro iterable - solo hace
`for keyVal in memtable.data:` - así que no hace falta tocar el código real
que se está probando. Esto da una ventana de escritura de duración
controlada por nosotros (no por el disco), así que el proceso padre puede
esperar a "started.marker" con total fiabilidad.
"""
import sys
import time
from pathlib import Path

from lsm.memtable import Memtable
from lsm.sstable import writeSSTable


class SlowData:
    def __init__(self, items, markerPath, delay):
        self.items = items
        self.markerPath = markerPath
        self.delay = delay

    def __iter__(self):
        self.markerPath.write_text("started")
        for item in self.items:
            time.sleep(self.delay)
            yield item


def main():
    target = Path(sys.argv[1])
    marker = Path(sys.argv[2])
    n = int(sys.argv[3])
    delay = float(sys.argv[4])

    items = [[f"key{i:08d}", f"value{i}"] for i in range(n)]
    m = Memtable()
    m.data = SlowData(items, marker, delay)
    writeSSTable(m, target)


if __name__ == "__main__":
    main()