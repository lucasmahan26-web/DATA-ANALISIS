"""
Verifica la mitad SQL de la guia SQL -> DAX (proyectos/03_powerbi/01_sql_a_dax.md).

Por que existe:
  DAX no se puede verificar desde aca: hace falta Power BI Desktop. Y una guia de
  DAX con formulas equivocadas es peor que no tener guia, porque el principiante
  no puede distinguir "mi error" de "el error del material".

  Lo que SI se puede verificar es la mitad SQL de cada par: que cada consulta
  ejecute y devuelva un numero con sentido. Eso garantiza que el patron que la
  persona ya sabe leer en SQL este bien definido, y que el DAX sea su traduccion
  directa.

  La verificacion del DAX queda explicitamente del lado del alumno: se hace
  cargando el modelo en Power BI y comparando contra estos mismos numeros.

Ejecutar:  <python> scripts/verificar_sql_a_dax.py
Requiere:  datos/bar/analisis_bar.db
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datos" / "bar" / "analisis_bar.db"

# (n, titulo, SQL equivalente, indice de la columna a mostrar como "valor")
CASOS: list[tuple[int, str, str]] = [
    (1, "Total vendido",
     "SELECT ROUND(SUM(importe), 0) AS total FROM ventas"),
    (2, "Total filtrado por dimension",
     "SELECT ROUND(SUM(v.importe), 0) AS total FROM ventas v "
     "JOIN carta c ON c.id_trago = v.id_trago WHERE c.categoria = 'Cocteles'"),
    (3, "Conteo distinto",
     "SELECT COUNT(DISTINCT id_insumo) AS insumos_distintos FROM recetas"),
    (4, "Promedio por fila",
     "SELECT ROUND(AVG(importe), 0) AS ticket_promedio FROM ventas"),
    (5, "Participacion sobre el total",
     "SELECT c.categoria, ROUND(SUM(v.importe), 0) AS total, "
     "ROUND(100.0 * SUM(v.importe) / (SELECT SUM(importe) FROM ventas), 1) AS pct "
     "FROM ventas v JOIN carta c ON c.id_trago = v.id_trago "
     "GROUP BY c.categoria ORDER BY total DESC"),
    (6, "Acumulado (running total) por semana",
     "WITH s AS (SELECT semana, SUM(importe) AS t FROM ventas GROUP BY semana) "
     "SELECT semana, ROUND(t, 0) AS semana_t, "
     "ROUND(SUM(t) OVER (ORDER BY semana), 0) AS acumulado FROM s ORDER BY semana"),
    (7, "Periodo anterior (LAG) por mes",
     "WITH s AS (SELECT cal.mes, SUM(v.importe) AS t FROM ventas v "
     "JOIN calendario cal ON cal.fecha = v.fecha GROUP BY cal.mes) "
     "SELECT mes, ROUND(t, 0) AS t, ROUND(LAG(t) OVER (ORDER BY mes), 0) AS mes_previo "
     "FROM s ORDER BY mes"),
    (8, "Variacion % periodo a periodo",
     "WITH s AS (SELECT cal.mes, SUM(v.importe) AS t FROM ventas v "
     "JOIN calendario cal ON cal.fecha = v.fecha GROUP BY cal.mes), "
     "c AS (SELECT mes, t, LAG(t) OVER (ORDER BY mes) AS previo FROM s) "
     "SELECT mes, ROUND(100.0 * (t - previo) / previo, 1) AS var_pct "
     "FROM c WHERE previo IS NOT NULL ORDER BY mes"),
    (9, "Ranking global (RANK)",
     "SELECT id_trago, ROUND(SUM(importe), 0) AS t, "
     "RANK() OVER (ORDER BY SUM(importe) DESC) AS posicion "
     "FROM ventas GROUP BY id_trago ORDER BY posicion LIMIT 5"),
    (10, "Top N dentro de cada grupo (ROW_NUMBER + PARTITION BY)",
     "WITH r AS (SELECT categoria, nombre_insumo, costo_actual, "
     "ROW_NUMBER() OVER (PARTITION BY categoria ORDER BY costo_actual DESC) AS rn "
     "FROM insumos) SELECT categoria, nombre_insumo, ROUND(costo_actual, 0) AS costo "
     "FROM r WHERE rn <= 2 ORDER BY categoria"),
    (11, "Cantidad de filas (COUNTROWS)",
     "SELECT COUNT(*) AS filas FROM ventas"),
    (12, "Condicional (SUM + CASE)",
     "SELECT ROUND(SUM(CASE WHEN cal.dia_semana IN ('Sabado', 'Domingo') "
     "THEN v.importe ELSE 0 END), 0) AS fin_de_semana, "
     "ROUND(SUM(CASE WHEN cal.dia_semana NOT IN ('Sabado', 'Domingo') "
     "THEN v.importe ELSE 0 END), 0) AS entre_semana "
     "FROM ventas v JOIN calendario cal ON cal.fecha = v.fecha"),
]

# Control de cordura: algunos valores tienen que ser exactamente estos.
CONTROLES = {
    1: 253_648_500,     # total facturado del periodo
    11: 7941,           # filas de ventas (COUNT(*))
    # 38 insumos distintos, NO 61: 61 son las FILAS de recetas. Es la diferencia
    # entre COUNT(*) y COUNT(DISTINCT) — el error clasico que esta guia ensena.
    3: 38,
}


def main() -> int:
    if not DB.exists():
        sys.exit(f"[!] No existe {DB}. Ejecutá scripts/generar_dataset_bar.py")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    fallos: list[str] = []
    resultados: dict[int, str] = {}

    print(f"[i] {len(CASOS)} patrones SQL -> DAX\n")
    for n, titulo, sql in CASOS:
        try:
            filas = con.execute(sql).fetchall()
        except sqlite3.Error as e:
            fallos.append(f"#{n}: {e}")
            print(f"  {n:>2}. {titulo:<42} ERROR: {e}")
            continue

        if not filas:
            fallos.append(f"#{n}: devuelve 0 filas")
            print(f"  {n:>2}. {titulo:<42} 0 FILAS")
            continue

        # Resumen legible para la guia
        def fmt(v) -> str:
            if isinstance(v, float):
                return f"{v:,.1f}".replace(",", ".")
            if isinstance(v, int):
                return f"{v:,}".replace(",", ".")
            return str(v)

        if len(filas) == 1 and len(filas[0]) == 1:
            resumen = fmt(filas[0][0])
        elif len(filas) == 1:
            resumen = "  ".join(fmt(v) for v in filas[0])
        else:
            primera = " | ".join(fmt(v) for v in filas[0])
            ultima = " | ".join(fmt(v) for v in filas[-1])
            resumen = f"{len(filas)} filas: [{primera}] … [{ultima}]"
        resultados[n] = resumen

        # Control de cordura donde corresponde
        if n in CONTROLES:
            obtenido = filas[0][0]
            if int(obtenido) != CONTROLES[n]:
                fallos.append(f"#{n}: {obtenido} != {CONTROLES[n]}")
                print(f"  {n:>2}. {titulo:<42} REVISAR {resumen}")
                continue

        print(f"  {n:>2}. {titulo:<42} {resumen}")

    con.close()

    if fallos:
        print(f"\n[!] FALLOS: {fallos}", file=sys.stderr)
        return 1
    print(f"\n[OK] Los {len(CASOS)} patrones SQL ejecutan y los controles de cordura pasan.")
    print("[i] La verificacion del DAX correspondiente queda a cargo del alumno en "
          "Power BI Desktop (ver la seccion 'Como verificar tu DAX' de la guia).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
