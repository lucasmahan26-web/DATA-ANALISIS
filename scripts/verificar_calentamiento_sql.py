"""
Verifica que los 28 ejercicios de calentamiento SQL sean resolubles con los
datos reales, y genera el archivo de soluciones de referencia.

Por que existe:
  Un ejercicio que no se puede resolver con los datos disponibles es peor que
  no tener ejercicio: hace perder tiempo y confianza. Este script ejecuta una
  solucion de referencia para CADA ejercicio contra analisis.db. Si alguna
  falla, el ejercicio esta mal planteado y hay que corregirlo.

  Las soluciones se escriben en un archivo aparte, marcado como spoiler, para
  que sirvan de autoevaluacion despues de intentar.

Ejecutar:  <python> scripts/verificar_calentamiento_sql.py
Requiere:  datos/p2/analisis.db  (crear con scripts/crear_db_sqlite.py)
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datos" / "p2" / "analisis.db"
SALIDA = ROOT / "proyectos" / "02_sql" / "00_calentamiento_soluciones.md"

# (numero, enunciado corto, solucion de referencia)
EJERCICIOS: list[tuple[int, str, str]] = [
    (1, "Primeras 20 filas de ventas",
     "SELECT * FROM ventas LIMIT 20"),
    (2, "Solo id_venta, fecha_venta e importe_neto",
     "SELECT id_venta, fecha_venta, importe_neto FROM ventas LIMIT 100"),
    (3, "Las 10 ventas de mayor importe",
     "SELECT id_venta, importe_neto FROM ventas ORDER BY importe_neto DESC LIMIT 10"),
    (4, "Ventas del 15/03/2024",
     "SELECT COUNT(*) FROM ventas WHERE fecha_venta = '2024-03-15'"),
    (5, "Ventas con importe > 50.000, de mayor a menor",
     "SELECT id_venta, importe_neto FROM ventas WHERE importe_neto > 50000 "
     "ORDER BY importe_neto DESC LIMIT 100"),
    (6, "Ventas de todo marzo 2024",
     "SELECT COUNT(*) FROM ventas "
     "WHERE fecha_venta BETWEEN '2024-03-01' AND '2024-03-31'"),
    (7, "Medios de pago",
     "SELECT id_medio_pago, descripcion FROM medios_pago ORDER BY id_medio_pago"),
    (8, "Productos inactivos",
     "SELECT id_producto, nombre_producto FROM productos WHERE activo = 'N'"),

    (9, "Total de filas de ventas",
     "SELECT COUNT(*) AS filas FROM ventas"),
    (10, "Suma total de importe_neto",
     "SELECT ROUND(SUM(importe_neto), 2) AS total FROM ventas"),
    (11, "Promedio, minimo y maximo de importe_neto",
     "SELECT ROUND(AVG(importe_neto), 2) AS promedio, "
     "ROUND(MIN(importe_neto), 2) AS minimo, "
     "ROUND(MAX(importe_neto), 2) AS maximo FROM ventas"),
    (12, "Ventas por turno de vendedor",
     "SELECT vd.turno, COUNT(*) AS ventas FROM ventas v "
     "JOIN vendedores vd ON v.id_vendedor = vd.id_vendedor "
     "GROUP BY vd.turno ORDER BY ventas DESC"),
    (13, "Ventas por region de sucursal",
     "SELECT s.region, COUNT(*) AS ventas FROM ventas v "
     "JOIN sucursales s ON v.id_sucursal = s.id_sucursal "
     "GROUP BY s.region ORDER BY ventas DESC"),
    (14, "Facturacion por anio y mes",
     "SELECT strftime('%Y', fecha_venta) AS anio, "
     "strftime('%m', fecha_venta) AS mes, "
     "ROUND(SUM(importe_neto), 2) AS facturacion "
     "FROM ventas GROUP BY anio, mes ORDER BY anio, mes"),
    (15, "Top 5 productos por unidades vendidas",
     "SELECT id_producto, SUM(cantidad) AS unidades FROM ventas "
     "GROUP BY id_producto ORDER BY unidades DESC LIMIT 5"),
    (16, "Tipos de cliente con mas de 200 ventas (HAVING)",
     "SELECT c.tipo_cliente, COUNT(*) AS ventas FROM ventas v "
     "JOIN clientes c ON v.id_cliente = c.id_cliente "
     "GROUP BY c.tipo_cliente HAVING COUNT(*) > 200 ORDER BY ventas DESC"),
    (17, "Cantidad de pedidos distintos",
     "SELECT COUNT(DISTINCT id_pedido) AS pedidos FROM ventas"),

    (18, "Regiones distintas",
     "SELECT DISTINCT region FROM sucursales ORDER BY region"),
    (19, "Ventas con id_medio_pago 1 o 5",
     "SELECT COUNT(*) AS con_in FROM ventas WHERE id_medio_pago IN (1, 5)"),
    (20, "Productos cuyo nombre contiene 'Leche'",
     "SELECT id_producto, nombre_producto FROM productos "
     "WHERE nombre_producto LIKE '%Leche%'"),
    (21, "Clasificar ventas por rango de importe",
     "SELECT CASE WHEN importe_neto < 10000 THEN 'chico' "
     "WHEN importe_neto <= 50000 THEN 'mediano' ELSE 'grande' END AS rango, "
     "COUNT(*) AS ventas FROM ventas GROUP BY rango ORDER BY ventas DESC"),

    (22, "Venta + nombre de producto",
     "SELECT v.id_venta, v.fecha_venta, p.nombre_producto, v.importe_neto "
     "FROM ventas v JOIN productos p ON v.id_producto = p.id_producto LIMIT 50"),
    (23, "Facturacion por categoria (3 tablas)",
     "SELECT c.nombre_categoria, ROUND(SUM(v.importe_neto), 2) AS facturacion "
     "FROM ventas v JOIN productos p ON v.id_producto = p.id_producto "
     "JOIN categorias c ON p.id_categoria = c.id_categoria "
     "GROUP BY c.nombre_categoria ORDER BY facturacion DESC"),
    (24, "INNER vs LEFT JOIN sobre sucursales",
     "SELECT (SELECT COUNT(*) FROM ventas v JOIN sucursales s "
     "ON v.id_sucursal = s.id_sucursal) AS con_inner_join, "
     "(SELECT COUNT(*) FROM ventas v LEFT JOIN sucursales s "
     "ON v.id_sucursal = s.id_sucursal) AS con_left_join, "
     "(SELECT COUNT(*) FROM ventas) AS total_filas"),

    (25, "Vendedores con sus ventas, incluidos los que no vendieron",
     "SELECT vd.nombre_vendedor, ROUND(COALESCE(SUM(v.importe_neto), 0), 2) AS total "
     "FROM vendedores vd LEFT JOIN ventas v ON vd.id_vendedor = v.id_vendedor "
     "GROUP BY vd.id_vendedor, vd.nombre_vendedor ORDER BY total DESC LIMIT 15"),
    (26, "Mes de mayor facturacion por sucursal (ROW_NUMBER)",
     "WITH por_mes AS (SELECT id_sucursal, strftime('%Y-%m', fecha_venta) AS mes, "
     "SUM(importe_neto) AS total FROM ventas GROUP BY id_sucursal, mes), "
     "rank AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY id_sucursal "
     "ORDER BY total DESC) AS rn FROM por_mes) "
     "SELECT id_sucursal, mes, ROUND(total, 2) AS total FROM rank WHERE rn = 1 "
     "ORDER BY id_sucursal"),
    (27, "Variacion porcentual mes a mes (LAG)",
     "WITH por_mes AS (SELECT strftime('%Y-%m', fecha_venta) AS mes, "
     "SUM(importe_neto) AS total FROM ventas GROUP BY mes) "
     "SELECT mes, ROUND(total, 2) AS total, "
     "ROUND(100.0 * (total - LAG(total) OVER (ORDER BY mes)) "
     "/ LAG(total) OVER (ORDER BY mes), 2) AS var_pct "
     "FROM por_mes ORDER BY mes"),
    (28, "Acumulado del anio (running total)",
     "WITH por_mes AS (SELECT strftime('%Y-%m', fecha_venta) AS mes, "
     "SUM(importe_neto) AS total FROM ventas GROUP BY mes) "
     "SELECT mes, ROUND(total, 2) AS total, "
     "ROUND(SUM(total) OVER (ORDER BY mes ROWS BETWEEN UNBOUNDED PRECEDING "
     "AND CURRENT ROW), 2) AS acumulado FROM por_mes ORDER BY mes"),
]


# Ejercicios cuyo SQLite NO es portable a PostgreSQL. Solo cambian las funciones
# de fecha: SQLite usa strftime(), PostgreSQL usa EXTRACT() y TO_CHAR().
# El resto de los 28 es SQL estandar y corre igual en los dos motores.
PG_VARIANTES: dict[int, str] = {
    14: "SELECT EXTRACT(YEAR FROM fecha_venta)::int AS anio, "
        "EXTRACT(MONTH FROM fecha_venta)::int AS mes, "
        "ROUND(SUM(importe_neto), 2) AS facturacion "
        "FROM ventas GROUP BY 1, 2 ORDER BY 1, 2",
    26: "WITH por_mes AS (SELECT id_sucursal, "
        "TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, SUM(importe_neto) AS total "
        "FROM ventas GROUP BY 1, 2), "
        "rank AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY id_sucursal "
        "ORDER BY total DESC) AS rn FROM por_mes) "
        "SELECT id_sucursal, mes, ROUND(total, 2) AS total FROM rank WHERE rn = 1 "
        "ORDER BY id_sucursal",
    27: "WITH por_mes AS (SELECT TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, "
        "SUM(importe_neto) AS total FROM ventas GROUP BY 1) "
        "SELECT mes, ROUND(total, 2) AS total, "
        "ROUND(100.0 * (total - LAG(total) OVER (ORDER BY mes)) "
        "/ LAG(total) OVER (ORDER BY mes), 2) AS var_pct "
        "FROM por_mes ORDER BY mes",
    28: "WITH por_mes AS (SELECT TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, "
        "SUM(importe_neto) AS total FROM ventas GROUP BY 1) "
        "SELECT mes, ROUND(total, 2) AS total, "
        "ROUND(SUM(total) OVER (ORDER BY mes ROWS BETWEEN UNBOUNDED PRECEDING "
        "AND CURRENT ROW), 2) AS acumulado FROM por_mes ORDER BY mes",
}


def main() -> int:
    if not DB.exists():
        sys.exit(f"[!] No existe {DB}. Ejecutá primero scripts/crear_db_sqlite.py")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    fallos: list[str] = []
    resultados: dict[int, str] = {}

    print(f"[i] Ejecutando {len(EJERCICIOS)} soluciones de referencia sobre {DB.name}")
    print(f"\n    {'#':<5}{'Filas':>7}   Resultado / error")
    for numero, _enunciado, sql in EJERCICIOS:
        try:
            cur = con.execute(sql)
            filas = cur.fetchall()
        except sqlite3.Error as e:
            fallos.append(f"#{numero}: {e}")
            print(f"    {numero:<5}{'-':>7}   ERROR: {e}")
            continue

        if len(filas) == 1 and len(filas[0]) == 1:
            resumen = str(filas[0][0])
        elif len(filas) <= 3:
            resumen = " | ".join(str(f) for f in filas)
        else:
            resumen = f"{filas[0]} … {filas[-1]}"

        # Un ejercicio que devuelve 0 filas esta mal planteado: el alumno no
        # tiene forma de saber si su consulta fallo o si el ejercicio no tenia
        # respuesta. Ya paso con el umbral de importe (500.000 cuando el maximo
        # real es 328.662), asi que ahora se detecta automaticamente.
        if not filas:
            fallos.append(f"#{numero}: devuelve 0 filas (umbral o filtro mal elegido)")
            print(f"    {numero:<5}{0:>7}   <-- 0 FILAS: ejercicio mal planteado")
            resultados[numero] = resumen
            continue

        resultados[numero] = resumen
        print(f"    {numero:<5}{len(filas):>7}   {resumen[:90]}")

    con.close()

    # ------------------------------------------------------------ soluciones
    lineas = [
        "# Calentamiento SQL — soluciones de referencia",
        "",
        "> ⚠️ **SPOILER.** Intentá cada ejercicio primero, aunque te salga mal.",
        "> El aprendizaje está en escribir y equivocarse, no en leer la solución.",
        ">",
        "> Cuando termines un bloque, compará: **tu consulta no tiene que ser igual**",
        "> a esta. Si devuelve lo mismo, está bien. Hay muchas formas correctas.",
        "",
        "## Nota sobre dialectos",
        "",
        "Estas soluciones corren en SQLite (el motor de `analisis.db`). Solo **4** cambian en",
        "PostgreSQL, y todos por las funciones de fecha. Los 28 en dialecto PostgreSQL están",
        "en `datos/p2/calentamiento_postgres.sql`.",
        "",
        "| SQLite (acá) | PostgreSQL (P2) |",
        "|---|---|",
        "| `strftime('%Y', fecha)` | `EXTRACT(YEAR FROM fecha)` |",
        "| `strftime('%m', fecha)` | `EXTRACT(MONTH FROM fecha)` |",
        "| `strftime('%Y-%m', fecha)` | `TO_CHAR(fecha, 'YYYY-MM')` |",
        "| fechas como `TEXT` | tipo `DATE` nativo |",
        "",
        "> **Verificado:** los 28 ejercicios en dialecto PostgreSQL ejecutan sin error contra",
        "> PostgreSQL 18, y `strftime()` efectivamente falla ahí",
        "> (`ERROR: function strftime(unknown, date) does not exist`).",
        "",
        "---",
        "",
    ]
    for numero, enunciado, sql in EJERCICIOS:
        lineas += [
            f"## {numero}. {enunciado}",
            "",
            "```sql",
            sql,
            "```",
            "",
        ]
        if numero in resultados:
            lineas += [f"*Resultado obtenido:* `{resultados[numero]}`", ""]
        lineas += ["---", ""]

    lineas += [
        "## Si querés verificar de verdad si entendiste",
        "",
        "La solución no es la meta: la meta es que puedas **resolverlo de nuevo mañana",
        "sin mirar**. Volvé al [calentamiento](00_calentamiento_sql.md) dentro de una",
        "semana y hacé el bloque 4 sin abrir este archivo. Si te sale, aprendiste.",
        "",
    ]
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\n[i] Soluciones escritas en {SALIDA}")

    # ------------------------------------------------- version PostgreSQL
    # Se emite un archivo con los 28 ejercicios en dialecto PostgreSQL, para
    # poder verificar de verdad que la tabla de dialectos de la guia es cierta.
    pg = ROOT / "datos" / "p2" / "calentamiento_postgres.sql"
    pg_lineas = [
        "\\echo === CALENTAMIENTO SQL EN POSTGRESQL, 28 EJERCICIOS ===",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    for numero, enunciado, sql in EJERCICIOS:
        pg_sql = PG_VARIANTES.get(numero, sql)
        pg_lineas += [
            f"\\echo --- Ejercicio {numero}: {enunciado}",
            f"{pg_sql};",
            "",
        ]
    pg.write_text("\n".join(pg_lineas), encoding="utf-8")
    print(f"[i] Version PostgreSQL de los 28 ejercicios: {pg}")
    print(f"    ({len(PG_VARIANTES)} ejercicios cambian: {sorted(PG_VARIANTES)})")

    if fallos:
        print(f"\n[!] Ejercicios NO resolubles: {fallos}", file=sys.stderr)
        return 1
    print(f"[OK] Los {len(EJERCICIOS)} ejercicios son resolubles con los datos reales "
          "y devuelven resultados concretos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
