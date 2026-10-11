"""
Verificacion end-to-end del dataset del bar, usando un motor SQL real (SQLite).

Que valida:
  1. Que el reporte de variacion publicado en la clave EJECUTE y no devuelva NULL.
  2. Que el ranking por PESOS ponga arriba los 3 SKU robados (la metrica correcta).
  3. Que el ranking por MILILITROS NO los ponga arriba (la metrica enganosa).
  4. Que el par +/- del error de conteo sea detectable en la serie semanal.
  5. Que la variacion negativa del remito no cargado sea detectable.
  6. Que el over-pouring sea parejo (~6%) en toda la cocteleria.

Busca el bloque SQL correcto por su contenido, no por su posicion: la clave tiene
un bloque anterior con el ejemplo INCORRECTO de la trampa LAG/WHERE.

Ejecutar:  <python> scripts/verificar_bar_sql.py
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datos" / "bar" / "analisis_bar.db"
CLAVE = ROOT / "datos" / "bar" / "BAR_CLAVE_NO_ABRIR.md"

# Lo que se inyecto (debe coincidir con generar_dataset_bar.py)
ROBO = {"Whisky premium 12 anios": 350, "Tequila reposado": 350, "Mezcal artesanal": 350}
INSUMO_CONTEO, SEM_CONTEO = "Ron blanco", 12
INSUMO_REMITO, SEM_REMITO = "Gin London Dry", 8


def main() -> int:
    if not DB.exists():
        sys.exit(f"[!] No existe {DB}. Ejecutá scripts/generar_dataset_bar.py")

    texto = CLAVE.read_text(encoding="utf-8")
    bloques = re.findall(r"```sql\n(.*?)```", texto, re.S)
    # El reporte de variacion es el bloque que proyecta variacion_pesos.
    candidatos = [b.strip().rstrip(";") for b in bloques if "variacion_pesos AS" in b
                  or "variacion_pesos," in b or "variacion_pesos\n" in b]
    if not candidatos:
        sys.exit("[!] No encuentro el reporte de variacion en la clave")
    sql_var = candidatos[0]
    print(f"[i] Bloques SQL en la clave: {len(bloques)} | reporte de variacion: "
          f"{len(sql_var.splitlines())} lineas")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    fallos: list[str] = []

    # ---------------------------------------------------- 1. ejecuta sin NULL
    filas = con.execute(sql_var).fetchall()
    nulos = sum(1 for f in filas if f[6] is None or f[7] is None)
    print(f"\n[1] Reporte de variacion: {len(filas)} filas x {len(filas[0])} columnas")
    print(f"    Filas con variacion NULL: {nulos}")
    if nulos:
        fallos.append(f"{nulos} filas con variacion NULL (trampa LAG/WHERE)")
    if len(filas[0]) != 8:
        fallos.append(f"se esperaban 8 columnas, hay {len(filas[0])}")

    def con_cte(select: str):
        return con.execute(f"WITH variacion AS ({sql_var}) {select}").fetchall()

    # ------------------------------------------- 2. ranking por PESOS (correcto)
    top_pesos = con_cte(
        "SELECT nombre_insumo, SUM(variacion_pesos) AS p FROM variacion "
        "GROUP BY nombre_insumo ORDER BY p DESC LIMIT 5"
    )
    print("\n[2] Top 5 por VARIACION EN PESOS (deberia liderar el robo):")
    for n, p in top_pesos:
        print(f"    {n:<28}{p:>14,.0f} $")
    top3_pesos = {n for n, _p in top_pesos[:3]}
    if not set(ROBO).issubset(top3_pesos):
        fallos.append(f"robo no detectable por pesos: {sorted(top3_pesos)}")

    # ------------------------------------- 3. ranking por ML (debe ser distinto)
    top_ml = con_cte(
        "SELECT nombre_insumo, SUM(variacion_ml) AS v FROM variacion "
        "GROUP BY nombre_insumo ORDER BY v DESC LIMIT 5"
    )
    print("\n[3] Top 5 por VARIACION EN MILILITROS (deberia NO mostrar el robo):")
    for n, v in top_ml:
        print(f"    {n:<28}{v:>14,.0f} ml")
    if set(ROBO).issubset({n for n, _v in top_ml[:3]}):
        print("    [i] Advertencia: el robo tambien domina por ml; el contraste "
              "pedagogico se pierde")

    # ---------------------------------- 4. par +/- del error de conteo (C3)
    serie = con_cte(
        f"SELECT semana, variacion_ml FROM variacion WHERE nombre_insumo = "
        f"'{INSUMO_CONTEO}' ORDER BY semana"
    )
    dic = {s: v for s, v in serie}
    base = dic.get(SEM_CONTEO - 1, 0)
    pico = dic.get(SEM_CONTEO, 0)
    post = dic.get(SEM_CONTEO + 1, 0)
    print(f"\n[4] C3 error de conteo en '{INSUMO_CONTEO}':")
    print(f"    semana {SEM_CONTEO - 1}: {base:>+12,.0f} ml")
    print(f"    semana {SEM_CONTEO}:     {pico:>+12,.0f} ml  <-- pico")
    print(f"    semana {SEM_CONTEO + 1}: {post:>+12,.0f} ml  <-- compensacion")
    if not (pico > base and post < base):
        fallos.append(f"C3 sin par +/-: {base:.0f} / {pico:.0f} / {post:.0f}")

    # ------------------------- 5. variacion negativa del remito no cargado (C5)
    serie_c5 = con_cte(
        f"SELECT semana, variacion_ml FROM variacion WHERE nombre_insumo = "
        f"'{INSUMO_REMITO}' ORDER BY semana"
    )
    d5 = {s: v for s, v in serie_c5}
    c5 = d5.get(SEM_REMITO, 0)
    print(f"\n[5] C5 remito no cargado en '{INSUMO_REMITO}':")
    print(f"    semana {SEM_REMITO}: {c5:>+12,.0f} ml  (uso negativo = falta un papel)")
    if c5 >= 0:
        fallos.append(f"C5 no da variacion negativa: {c5:.0f}")

    # ------------------------------ 6. over-pouring parejo en la cocteleria (C1)
    pcts = con_cte(
        "SELECT ROUND(100.0 * variacion_ml / uso_teorico_ml, 1) FROM variacion "
        "WHERE uso_teorico_ml > 0 AND id_insumo IN ("
        "  SELECT DISTINCT r.id_insumo FROM recetas r JOIN carta c ON c.id_trago = r.id_trago"
        "  WHERE c.categoria = 'Cocteles')"
    )
    valores = sorted(v for (v,) in pcts)
    mediana = valores[len(valores) // 2]
    print(f"\n[6] C1 over-pouring: mediana de variacion % en cocteleria = {mediana:.1f}% "
          "(esperado ~6.0%)")
    if abs(mediana - 6.0) > 3:
        fallos.append(f"over-pouring fuera de rango: {mediana:.1f}%")

    # ------------------------------------- 7. merma total y % sobre las ventas
    total_merma = con_cte("SELECT ROUND(SUM(variacion_pesos), 0) FROM variacion")[0][0]
    total_ventas = con.execute("SELECT ROUND(SUM(importe), 0) FROM ventas").fetchone()[0]
    print(f"\n[7] Merma total del periodo: {total_merma:,.0f} $ "
          f"({100 * total_merma / total_ventas:.2f}% de las ventas)")

    con.close()

    if fallos:
        print(f"\n[!] FALLOS: {fallos}", file=sys.stderr)
        return 1
    print("\n[OK] El reporte de variacion de la clave ejecuta sin NULL y recupera "
          "las 5 causas con la metrica correcta (pesos).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
