"""
Crea la base SQLite `datos/p2/analisis.db` a partir de los 7 CSV del Proyecto 2.

Para que sirve:
  DBeaver es un CLIENTE, no un motor de base de datos. Sin un motor al que
  conectarse no se puede practicar SQL. Este script crea un archivo de base de
  datos SQLite que DBeaver abre directamente, sin instalar ni configurar nada.

  Es la via rapida para empezar a practicar HOY. PostgreSQL sigue siendo el
  objetivo del Proyecto 2 (es lo que piden las ofertas), pero esto desbloquea
  la practica de sintaxis de inmediato.

Los datos se cargan TAL CUAL: sin constraints y con los 15 defectos intactos.
El archivo es el punto de partida del diagnostico, no el resultado.

Ejecutar:  <python> scripts/crear_db_sqlite.py
Salida:    datos/p2/analisis.db
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "datos" / "p2"
DESTINO = P2 / "analisis.db"

TIPOS = {
    "categorias": {"id_categoria": "INTEGER", "nombre_categoria": "TEXT",
                   "departamento": "TEXT"},
    "productos": {"id_producto": "INTEGER", "nombre_producto": "TEXT",
                  "id_categoria": "INTEGER", "precio_lista": "REAL",
                  "activo": "TEXT", "fecha_alta": "TEXT"},
    "sucursales": {"id_sucursal": "INTEGER", "nombre_sucursal": "TEXT",
                   "region": "TEXT", "provincia": "TEXT",
                   "zona_comercial": "TEXT", "fecha_apertura": "TEXT"},
    "vendedores": {"id_vendedor": "INTEGER", "nombre_vendedor": "TEXT",
                   "id_sucursal": "INTEGER", "fecha_ingreso": "TEXT",
                   "turno": "TEXT"},
    "clientes": {"id_cliente": "INTEGER", "razon_social": "TEXT",
                 "tipo_cliente": "TEXT", "ciudad": "TEXT",
                 "provincia": "TEXT", "fecha_alta": "TEXT"},
    "medios_pago": {"id_medio_pago": "INTEGER", "descripcion": "TEXT"},
    "ventas": {"id_venta": "INTEGER", "id_pedido": "TEXT", "fecha_venta": "TEXT",
               "id_producto": "INTEGER", "id_sucursal": "INTEGER",
               "id_vendedor": "INTEGER", "id_cliente": "INTEGER",
               "id_medio_pago": "INTEGER", "cantidad": "INTEGER",
               "precio_unitario": "REAL", "descuento": "REAL",
               "importe_neto": "REAL"},
}

ESPERADO = {
    "categorias": 8, "productos": 57, "sucursales": 12, "vendedores": 40,
    "clientes": 312, "medios_pago": 5, "ventas": 130688,
}

DESTINO.unlink(missing_ok=True)
con = sqlite3.connect(DESTINO)

print(f"[1] Creando {DESTINO.name}")
for tabla, cols in TIPOS.items():
    defs = ", ".join(f"{c} {t}" for c, t in cols.items())
    con.execute(f"CREATE TABLE {tabla} ({defs})")

    origen = P2 / f"{tabla}.csv"
    if not origen.exists():
        sys.exit(f"[!] Falta {origen}. Ejecutá primero scripts/generar_dataset_p2.py")

    with origen.open("r", newline="", encoding="utf-8") as fh:
        lector = csv.reader(fh)
        cab = next(lector)
        filas = [[None if v == "" else v for v in fila] for fila in lector]

    marcas = ", ".join("?" * len(cab))
    con.executemany(f"INSERT INTO {tabla} ({', '.join(cab)}) VALUES ({marcas})", filas)
    print(f"    {tabla:<14}{len(filas):>8} filas")

con.commit()

# ---------------------------------------------------------------- verificar
print("\n[2] Verificacion re-leyendo la base creada")
fallos = []
for tabla, esperado in ESPERADO.items():
    real = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    ok = real == esperado
    if not ok:
        fallos.append(f"{tabla}: {real} != {esperado}")
    print(f"    {tabla:<14}{real:>8} / {esperado:<8} {'OK' if ok else 'REVISAR'}")

# El defecto mas visible, como prueba de que la base es la cruda y no una limpia
dups = con.execute(
    "SELECT SUM(c - 1) FROM (SELECT COUNT(*) AS c FROM ventas "
    "GROUP BY id_venta HAVING COUNT(*) > 1)"
).fetchone()[0]
print(f"\n[3] Prueba de que los datos vienen CRUDOS: id_venta duplicados = {dups} (esperado 180)")
if dups != 180:
    fallos.append(f"duplicados={dups}")

total = con.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
con.close()

tam = DESTINO.stat().st_size / 1024 / 1024
print(f"\n[4] Archivo creado: {DESTINO} ({tam:.1f} MB, {total} filas en ventas)")

if fallos:
    print(f"\n[!] FALLOS: {fallos}", file=sys.stderr)
    sys.exit(1)
print("\n[OK] Base lista para abrir en DBeaver.")
