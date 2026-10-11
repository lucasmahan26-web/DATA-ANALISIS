"""
Verifica que PRIMER_DIA.md sea correcto.

Un tutorial que dice "tu resultado tiene que ser X" y muestra un X equivocado es
peor que no tener tutorial: el principiante cree que se equivoco el, y abandona.

Que valida:
  1. Cada bloque ```sql del documento EJECUTA sin error.
  2. Los valores documentados coinciden con los que devuelve la base:
     - conteos 7941 / 73 / 1971
     - el top 5 de tragos por facturacion
     - la facturacion por dia de la semana
     - el hallazgo del 51,6% en Viernes + Sabado

Ejecutar:  <python> scripts/verificar_primer_dia.py
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datos" / "bar" / "analisis_bar.db"
GUIA = ROOT / "PRIMER_DIA.md"

# Lo que el documento afirma. Si la base no lo confirma, la guia miente.
TOP5_DOC = [
    ("Gin Tonic", 2999, 21_592_800),
    ("Fernet con Cola", 3179, 20_345_600),
    ("Mojito", 2330, 16_543_000),
    ("Negroni", 2021, 15_763_800),
    ("Vodka Tonic", 2210, 15_249_000),
]
DIAS_DOC = [
    ("Sabado", 69_681_500), ("Viernes", 61_202_100), ("Jueves", 32_976_400),
    ("Domingo", 29_282_300), ("Miercoles", 23_484_200), ("Martes", 18_901_500),
    ("Lunes", 18_120_500),
]
CONTEOS_DOC = {"ventas": 7941, "insumos": 73, "conteos": 1971}
HALLAZGO_DOC = 51.6


def main() -> int:
    for ruta in (DB, GUIA):
        if not ruta.exists():
            sys.exit(f"[!] No existe {ruta}")

    texto = GUIA.read_text(encoding="utf-8")
    bloques = [b.strip().rstrip(";") for b in re.findall(r"```sql\n(.*?)```", texto, re.S)]
    print(f"[i] Bloques SQL en la guia: {len(bloques)}")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    fallos: list[str] = []

    # ---------------------------------------------- 1. cada bloque ejecuta
    print("\n[1] Ejecucion de cada bloque de la guia")
    for i, sql in enumerate(bloques, 1):
        try:
            filas = con.execute(sql).fetchall()
            print(f"    Bloque {i}: OK, {len(filas)} filas")
        except sqlite3.Error as e:
            fallos.append(f"bloque {i}: {e}")
            print(f"    Bloque {i}: ERROR -> {e}")

    # ------------------------------------------------- 2. conteos documentados
    print("\n[2] Conteos documentados")
    for tabla, esperado in CONTEOS_DOC.items():
        real = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        ok = real == esperado
        if not ok:
            fallos.append(f"COUNT({tabla}) = {real}, la guia dice {esperado}")
        print(f"    {tabla:<10}{real:>7} / {esperado:<7} {'OK' if ok else 'FALLA'}")

    # ------------------------------------------------------ 3. top 5 de tragos
    print("\n[3] Top 5 tragos por facturacion")
    real_top = con.execute(
        "SELECT id_trago, SUM(cantidad), ROUND(SUM(importe), 0) FROM ventas "
        "GROUP BY id_trago ORDER BY 3 DESC LIMIT 5"
    ).fetchall()
    for (n_doc, u_doc, f_doc), (n, u, f) in zip(TOP5_DOC, real_top):
        ok = (n == n_doc and u == u_doc and int(f) == f_doc)
        if not ok:
            fallos.append(f"top5: doc={n_doc}/{u_doc}/{f_doc} real={n}/{u}/{f}")
        print(f"    {n:<24}{u:>6} u{f:>13,.0f}  {'OK' if ok else 'FALLA'}")

    # El detalle que la guia afirma: Fernet vende mas unidades pero factura menos
    fernet = next(r for r in real_top if r[0] == "Fernet con Cola")
    gin = next(r for r in real_top if r[0] == "Gin Tonic")
    afirmacion = fernet[1] > gin[1] and fernet[2] < gin[2]
    print(f"    Afirmacion 'Fernet vende mas unidades pero factura menos': "
          f"{'SE CUMPLE' if afirmacion else 'NO SE CUMPLE'}")
    if not afirmacion:
        fallos.append("la afirmacion de unidades vs facturacion no se cumple")

    # --------------------------------------------------- 4. facturacion por dia
    print("\n[4] Facturacion por dia de la semana")
    real_dias = con.execute(
        "SELECT cal.dia_semana, ROUND(SUM(v.importe), 0) FROM ventas v "
        "JOIN calendario cal ON cal.fecha = v.fecha "
        "GROUP BY cal.dia_semana ORDER BY 2 DESC"
    ).fetchall()
    for (n_doc, f_doc), (n, f) in zip(DIAS_DOC, real_dias):
        ok = (n == n_doc and int(f) == f_doc)
        if not ok:
            fallos.append(f"dias: doc={n_doc}/{f_doc} real={n}/{f}")
        print(f"    {n:<12}{f:>14,.0f}  {'OK' if ok else 'FALLA'}")

    if len(real_dias) != len(DIAS_DOC):
        fallos.append(f"la guia lista {len(DIAS_DOC)} dias, la base tiene {len(real_dias)}")

    # ------------------------------------------------------- 5. el hallazgo
    total = sum(f for _n, f in real_dias)
    top2 = sum(f for _n, f in real_dias[:2])
    pct = round(100.0 * top2 / total, 1)
    print(f"\n[5] Hallazgo: Viernes + Sabado = {top2:,.0f} de {total:,.0f} = {pct}% "
          f"(la guia dice {HALLAZGO_DOC}%)")
    if abs(pct - HALLAZGO_DOC) > 0.05:
        fallos.append(f"hallazgo: doc={HALLAZGO_DOC}% real={pct}%")

    con.close()

    if fallos:
        print(f"\n[!] LA GUIA NO COINCIDE CON LOS DATOS: {fallos}", file=sys.stderr)
        return 1
    print("\n[OK] Todos los bloques ejecutan y todos los resultados documentados en "
          "PRIMER_DIA.md coinciden con la base.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
