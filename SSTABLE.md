# Formato de SSTable

Archivo que se escribe una sola vez (volcado de una memtable) y nunca se modifica.
Tres bloques consecutivos: datos, índice, pie. Todos los enteros son little-endian.

## 1. Datos
Entradas ordenadas por clave ascendente, con el mismo formato que el WAL:

    tipo (1) | longitud clave (4) | clave | longitud valor (4) | valor

Tipo 0 = put, tipo 1 = delete (valor vacío). Los borrados se guardan: si se
omitieran, una clave borrada podría reaparecer desde una SSTable más antigua.

## 2. Índice
Una fila por entrada, en el mismo orden:

    longitud clave (4) | clave | posición (8)

`posición` es el byte del archivo donde empieza esa entrada.

## 3. Pie
Últimos 8 bytes del archivo: la posición donde empieza el índice.

## Lectura de una clave
1. Leer los últimos 8 bytes: dónde empieza el índice.
2. Leer desde ahí hasta (tamaño del archivo − 8) y cargar el índice en memoria.
3. Búsqueda binaria de la clave. Si no está, no está en esta SSTable.
4. Saltar a la posición indicada y leer una entrada con `readEntry`.

## Ejemplo calculado a mano
Entradas: put a=3, delete b, put carro=xy.

| Bytes | Contenido | Tamaño |
|---|---|---|
| 0–10 | entrada 1: put a=3 | 11 |
| 11–20 | entrada 2: delete b | 10 |
| 21–36 | entrada 3: put carro=xy | 16 |
| 37–49 | índice: a → 0 | 13 |
| 50–62 | índice: b → 11 | 13 |
| 63–79 | índice: carro → 21 | 17 |
| 80–87 | pie: 37 | 8 |

Total: 88 bytes.

## Limitaciones conocidas
- El índice completo se carga en memoria al leer.
- Sin checksum: una corrupción en mitad del archivo no se detecta.