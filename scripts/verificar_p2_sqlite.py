"""
Verificacion end-to-end del Proyecto 2 usando un MOTOR SQL REAL (SQLite).

Que hace, y por que es una verificacion valida:
  1. Lee `datos/p2/P2_CLAVE_NO_ABRIR.md` y extrae las consultas de diagnostico
     que ese archivo publica (no las reescribe: usa EXACTAMENTE las entregadas).
  2. Lee los conteos esperados de la tabla del mismo archivo.
  3. Carga los 7 CSV en SQLite con los tipos correctos.
  4. Ejecuta cada consulta y compara contra el conteo declarado.
  5. Comprueba que las restricciones de P2_02 realmente se disparen sobre los
     datos crudos (si no se dispararan, el ejercicio no tendria sentido).

Esto valida tres cosas a la vez: los CSV, las consultas entregadas y la clave.

Ejecutar:  <python> scripts/verificar_p2_sqlite.py
"""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "datos" / "p2"
CLAVE = P2 / "P2_CLAVE_NO_ABRIR.md"

# Tipos por columna. Fechas como TEXT ISO (comparan lexicograficamente igual).
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
ORDEN_CARGA = ["categorias", "medios_pago", "sucursales", "productos",
               "vendedores", "clientes", "ventas"]

# ---------------------------------------------------------------- leer la clave
texto = CLAVE.read_text(encoding="utf-8")

marca = "## Consultas de verificación"
if marca not in texto:
    sys.exit(f"[!] No encuentro la seccion '{marca}' en {CLAVE.name}")
resto = texto.split(marca, 1)[1]
bloque = re.search(r"```sql\n(.*?)```", resto, re.S)
if not bloque:
    sys.exit("[!] No encuentro el bloque ```sql de consultas de verificacion")
sql_block = bloque.group(1)

# Consultas esperadas, con su codigo
esperadas: dict[str, str] = {}
for trozo in sql_block.split(";"):
    trozo = trozo.strip()
    if not trozo:
        continue
    m = re.match(r"--\s*@codigo\s+([VD]\d+)", trozo)
    if not m:
        sys.exit(f"[!] Consulta sin etiqueta @codigo:\n{trozo[:120]}")
    esperadas[m.group(1)] = trozo

# Conteos declarados en la tabla del mismo archivo
declarados: dict[str, int] = {}
for linea in texto.splitlines():
    if not linea.startswith("|"):
        continue
    partes = [p.strip() for p in linea.split("|")]
    if len(partes) >= 5 and re.fullmatch(r"[VD]\d+", partes[1]):
        if partes[3].isdigit():
            declarados[partes[1]] = int(partes[3])

print(f"[i] Consultas extraidas de la clave : {len(esperadas)}")
print(f"[i] Conteos declarados en la clave  : {len(declarados)}")

if set(esperadas) != set(declarados):
    sys.exit(f"[!] La clave declara {sorted(declarados)} pero define consultas "
             f"para {sorted(esperadas)}")

# ---------------------------------------------------------------- cargar SQLite
def cargar(con: sqlite3.Connection, con_constraints: bool) -> dict[str, int]:
    tablas: dict[str, int] = {}
    for tabla in ORDEN_CARGA:
        cols = TIPOS[tabla]
        defs = ", ".join(f"{c} {t}" for c, t in cols.items())
        extra = ""
        if con_constraints:
            if tabla == "ventas":
                extra = (", PRIMARY KEY (id_venta),"
                         " FOREIGN KEY (id_producto) REFERENCES productos(id_producto),"
                         " FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal),"
                         " FOREIGN KEY (id_vendedor) REFERENCES vendedores(id_vendedor),"
                         " FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),"
                         " FOREIGN KEY (id_medio_pago) REFERENCES medios_pago(id_medio_pago)")
            elif tabla == "productos":
                extra = (", PRIMARY KEY (id_producto),"
                         " FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)")
            elif tabla == "vendedores":
                extra = (", PRIMARY KEY (id_vendedor),"
                         " FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)")
            else:
                pk = list(cols)[0]
                extra = f", PRIMARY KEY ({pk})"
        con.execute(f"CREATE TABLE {tabla} ({defs}{extra})")

        with (P2 / f"{tabla}.csv").open("r", newline="", encoding="utf-8") as fh:
            lector = csv.reader(fh)
            cab = next(lector)
            filas = []
            for fila in lector:
                # Cadena vacia -> None (equivalente al NULL '' del COPY)
                filas.append([None if v == "" else v for v in fila])
        marcas = ", ".join("?" * len(cab))
        con.executemany(f"INSERT INTO {tabla} ({', '.join(cab)}) VALUES ({marcas})",
                        filas)
        tablas[tabla] = len(filas)
    return tablas


print("\n[1] Carga en SQLite con tipos correctos")
con = sqlite3.connect(":memory:")
filas_tabla = cargar(con, con_constraints=False)
for t in ORDEN_CARGA:
    print(f"    {t:<14}{filas_tabla[t]:>8} filas")

# ------------------------------------------------------------- ejecutar consultas
print("\n[2] Ejecucion de las consultas de la clave contra el motor SQL")
print(f"    {'Cod':<7}{'Declarado':>11}{'SQL real':>10}   Resultado")
fallos: list[str] = []
for cod in sorted(esperadas, key=lambda c: (c[0], int(c[1:]))):
    cur = con.execute(esperadas[cod])
    obtenido = cur.fetchone()[0]
    obtenido = 0 if obtenido is None else int(obtenido)
    esperado = declarados[cod]
    ok = obtenido == esperado
    if not ok:
        fallos.append(f"{cod}: {obtenido} != {esperado}")
    print(f"    {cod:<7}{esperado:>11}{obtenido:>10}   {'OK' if ok else 'FALLA'}")

# --------------------------------------- comprobar que las constraints se disparen
print("\n[3] Las restricciones de P2_02 deben fallar sobre los datos crudos")
con2 = sqlite3.connect(":memory:")
con2.execute("PRAGMA foreign_keys = ON")
try:
    cargar(con2, con_constraints=True)
    print("    [!] La carga CON constraints no fallo: el ejercicio perderia sentido")
    fallos.append("constraints-no-se-disparan")
except sqlite3.IntegrityError as e:
    print(f"    OK  El motor rechaza la carga: {e}")

con.close()
con2.close()

if fallos:
    print(f"\n[!] FALLOS: {fallos}", file=sys.stderr)
    sys.exit(1)
print(f"\n[OK] Las {len(esperadas)} consultas de la clave reproducen exactamente "
      "los conteos declarados, y las constraints se disparan como se espera.")
