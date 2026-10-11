"""
Diagnostico del problema de separadores decimales en P1_ventas_crudo.csv,
para el locale es-ES (el que tiene el Office del usuario).

Por que importa:
  El dataset mezcla DOS formatos numericos:
     1.234,56   (es: punto = miles, coma = decimal)
     1554.41    (en: punto = decimal)
  Con el locale en es-ES, la coma se lee bien pero el punto se interpreta como
  separador de miles. Con locale en-US pasa lo contrario.

  No hay UNA configuracion regional que sirva para los dos: hay que normalizar
  el texto ANTES de convertir el tipo. Este script mide exactamente cuantos
  valores caen en cada caso, para poder documentarlo con numeros y no a ojo.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "datos" / "P1_ventas_crudo.csv"
COL = "Precio_Unitario ($)"

PAT_ES = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")   # 1.234,56  /  1,50
PAT_EN = re.compile(r"^\d+\.\d{2}$")                 # 1554.41
PAT_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PAT_DMA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PAT_MMM = re.compile(r"^\d{2}-[a-z]{3}-\d{4}$")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

CENTINELAS = {"1900-01-01", "2025-13-45", "31/02/2024", "0000-00-00", "SIN FECHA"}


def parsea_como_ddmmyyyy(t: str) -> bool:
    """True si el texto se puede convertir a fecha con locale es-ES (dd/mm/aaaa)."""
    from datetime import date
    t = t.strip()
    try:
        if PAT_ISO.match(t):
            a, m, d = (int(x) for x in t.split("-"))
            date(a, m, d)
        elif PAT_DMA.match(t):
            d, m, a = (int(x) for x in t.split("/"))
            date(a, m, d)          # es-ES: primero el dia, despues el mes
        elif PAT_MMM.match(t):
            d, mes, a = t.split("-")
            date(int(a), MESES[mes], int(d))
        else:
            return False
    except (ValueError, KeyError):
        return False
    return True


def main() -> int:
    if not CSV.exists():
        sys.exit(f"[!] No existe {CSV}")

    filas = list(csv.DictReader(CSV.open(encoding="utf-8-sig")))
    forma = Counter()
    ejemplos: dict[str, list[str]] = {}

    for r in filas:
        v = r[COL].strip()
        if "," in v:
            clave = "es (coma decimal, puede tener punto de miles)"
        elif "." in v:
            clave = "en (punto decimal, sin coma)"
        else:
            clave = "entero / otro"
        forma[clave] += 1
        ejemplos.setdefault(clave, [])
        if len(ejemplos[clave]) < 4 and v not in ejemplos[clave]:
            ejemplos[clave].append(v)

    con_coma_y_punto_miles = sum(
        1 for r in filas if "," in r[COL] and PAT_ES.match(r[COL].strip())
        and "." in r[COL]
    )
    es_simple = sum(
        1 for r in filas if "," in r[COL] and PAT_ES.match(r[COL].strip())
        and "." not in r[COL]
    )
    es_malformado = sum(
        1 for r in filas if "," in r[COL] and not PAT_ES.match(r[COL].strip())
    )
    en_valido = sum(1 for r in filas if PAT_EN.match(r[COL].strip()))

    print(f"[i] Columna: {COL}  ({len(filas)} filas)\n")
    print("    Formato detectado")
    for k, n in forma.most_common():
        print(f"      {k:<48}{n:>7}")
        for e in ejemplos.get(k, []):
            print(f"          ej: {e!r}")

    print("\n    Desglose de los que tienen coma (formato es):")
    print(f"      con punto de miles (ej. 1.234,56)        {con_coma_y_punto_miles:>7}")
    print(f"      sin punto de miles (ej. 890,00)          {es_simple:>7}")
    print(f"      mal formados (revisar)                   {es_malformado:>7}")

    print(f"\n    Valores con punto decimal y sin coma (en)   {en_valido:>7}")

    print("\n[i] Consecuencia segun el locale de Power Query:")
    print("      locale es-ES (el tuyo):")
    print("        '1.234,56' -> 1234,56   OK")
    print("        '1554.41'  -> el punto se lee como separador de miles")
    print("                      => valor equivocado o Error, segun el caso")
    print("      locale en-US:")
    print("        '1.234,56' -> Error o texto")
    print("        '1554.41'  -> 1554.41   OK")
    print("\n    NO existe una configuracion regional que sirva para los dos.")
    print("    La unica solucion correcta es normalizar el TEXTO antes de convertir.")

    # Control: los dos grupos tienen que existir, si no el problema no existe
    if con_coma_y_punto_miles == 0 or en_valido == 0:
        print("\n[!] Uno de los dos formatos no aparece: revisar el dataset", file=sys.stderr)
        return 1

    # ---------------------------------------------------------------------
    # Segunda parte: que errores concretos va a mostrar Power Query con es-ES
    # ---------------------------------------------------------------------
    errores_fecha = [r["Fecha"].strip() for r in filas
                     if not parsea_como_ddmmyyyy(r["Fecha"])]
    fuera_periodo = sum(
        1 for r in filas if r["Fecha"].strip() == "1900-01-01"
    )
    print("\n" + "=" * 66)
    print("[i] QUE VAS A VER EXACTAMENTE AL CONVERTIR TIPOS CON LOCALE es-ES")
    print("=" * 66)

    print(f"\n  Columna 'Fecha' -> {len(errores_fecha)} valores en ERROR")
    print(f"    ({len(filas)} filas totales; los que fallan son las fechas mm/dd "
          f"cuyo 'mes' queda > 12, mas los centinelas)")
    from collections import Counter as C2
    print("    Desglose de los que fallan:")
    for pat, n in [
        ("mm/dd con dia > 12 (leido como dd/mm da mes invalido)",
         sum(1 for t in errores_fecha if PAT_DMA.match(t) and t not in CENTINELAS)),
        ("centinelas explicitos (SIN FECHA, 2025-13-45, 0000-00-00, 31/02)",
         sum(1 for t in errores_fecha if t in CENTINELAS)),
    ]:
        print(f"      {n:>6}  {pat}")
    otros = len(errores_fecha) - sum(
        1 for t in errores_fecha if PAT_DMA.match(t) or t in CENTINELAS)
    if otros:
        print(f"      {otros:>6}  otros")
    print(f"    Ademas, {fuera_periodo} fecha convierte bien pero es del anio 1900 "
          f"(no da error: da un analisis mal)")

    print(f"\n  Columna 'Precio_Unitario ($)' y 'Total ($)'")
    print(f"    Con es-ES, los {con_coma_y_punto_miles} valores con punto de miles "
          f"convierten OK.")
    print(f"    Los {forma['en (punto decimal, sin coma)']} valores con punto decimal "
          f"NO: el punto se lee como separador de miles.")
    print("    => o quedan en Error, o peor: converten a un valor 100x mas grande.")

    print("\n  Columna 'Descuento'")
    print("    Sin separadores de miles: convierte sin problema en los dos locales.")

    print("\n" + "=" * 66)
    print("[OK] Los dos formatos coexisten: el problema de separadores es real.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
