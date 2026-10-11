"""
Verifica que las afirmaciones del manual de Power Query
(proyectos/01_excel_powerquery/01_manual_powerquery.md) coincidan con los datos.

Por que existe:
  Un manual que dice "hay 48 categorias distintas que deberian ser 8" y se equivoca
  hace que el alumno persiga un problema que no existe, o peor: que crea que ya
  limpio cuando no lo hizo. Las afirmaciones sobre los datos tienen que ser
  comprobables.

  Ademas valida un punto sutil: una fecha puede TENER formato valido y ser
  IMPOSIBLE igual (2025-13-45, 0000-00-00). Clasificar solo por formato esconde
  esos casos, y es el error que comete todo el mundo al diagnosticar.

Ejecutar:  <python> scripts/verificar_manual_powerquery.py
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "datos" / "P1_ventas_crudo.csv"

COL_PRECIO = "Precio_Unitario ($)"
COL_TOTAL = "Total ($)"

# Lo que el manual afirma. Si algun valor no coincide, el manual miente.
AFIRMACIONES = {
    "filas": 2935,
    "columnas": 14,
    "categorias_reales": 8,
    "categorias_distintas_crudas": 48,
    "sucursales_reales": 8,
    "vendedores_reales": 12,
    "formatos_de_fecha": 4,
    "precios_con_coma": 2054,
    "filas_con_nbsp": 33,
    "fechas_mm_dd_inequivocas": 36,
    # Numeros del problema de separadores decimales (seccion 6b del manual)
    "precios_es_con_miles": 1832,
    "precios_es_simple": 222,
    "precios_en_punto_decimal": 881,
    # Errores de conversion esperados con locale es-ES (seccion 0 y 6)
    "errores_fecha_es_es": 49,
}

# Valores centinela inyectados a proposito (defecto D4). No son fechas de ningun
# formato: son basura explicita.
CENTINELAS = {"1900-01-01", "2025-13-45", "31/02/2024", "0000-00-00", "SIN FECHA"}

CATEGORIAS_OFICIALES = [
    "Almacén", "Bebidas", "Lácteos", "Limpieza", "Carnes", "Panadería",
    "Frutas y Verduras", "Congelados",
]
SUCURSALES_OFICIALES = [
    "Central Rosario", "Sucursal Norte", "Sucursal Sur", "Mendoza Centro",
    "Cordoba Nueva", "La Plata", "Tucuman Shopping", "Bariloche",
]

PATRON_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATRON_DMA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PATRON_DMA_MMM = re.compile(r"^\d{2}-[a-z]{3}-\d{4}$")

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


def a_num(t: str) -> float:
    t = t.strip()
    if "," in t:
        return float(t.replace(".", "").replace(",", "."))
    return float(t)


def fecha_valida(t: str) -> bool:
    """True solo si el texto representa una fecha REAL y del periodo del negocio."""
    t = t.strip()
    try:
        if PATRON_ISO.match(t):
            a, m, d = (int(x) for x in t.split("-"))
            f = date(a, m, d)
        elif PATRON_DMA.match(t):
            d, m, a = (int(x) for x in t.split("/"))
            f = date(a, m, d)
        elif PATRON_DMA_MMM.match(t):
            d, mes, a = t.split("-")
            f = date(int(a), MESES[mes], int(d))
        else:
            return False
    except (ValueError, KeyError):
        return False
    return date(2023, 1, 1) <= f <= date(2024, 12, 31)


def fecha_valida_es_es(t: str) -> bool:
    """
    True si Power Query con locale es-ES puede CONVERTIR el texto a fecha.

    Es distinto de fecha_valida(): aca no importa si la fecha es del periodo del
    negocio, solo si el parseo funciona. '1900-01-01' parsea bien (no da error de
    conversion) pero esta fuera del periodo, y son dos problemas distintos.
    """
    t = t.strip()
    try:
        if PATRON_ISO.match(t):
            a, m, d = (int(x) for x in t.split("-"))
            date(a, m, d)
        elif PATRON_DMA.match(t):
            # es-ES lee dia/mes/aaaa. Si el segundo numero es > 12, falla.
            d, m, a = (int(x) for x in t.split("/"))
            date(a, m, d)
        elif PATRON_DMA_MMM.match(t):
            d, mes, a = t.split("-")
            date(int(a), MESES[mes], int(d))
        else:
            return False
    except (ValueError, KeyError):
        return False
    return True


def main() -> int:
    if not CSV.exists():
        sys.exit(f"[!] No existe {CSV}. Ejecutá scripts/generar_dataset_p1.py")

    filas = list(csv.DictReader(CSV.open(encoding="utf-8-sig")))
    fallos: list[str] = []
    med: dict[str, int] = {}

    med["filas"] = len(filas)
    med["columnas"] = len(filas[0])

    # --- categorias / sucursales / vendedores: cuantos valores distintos HAY vs
    # --- cuantos DEBERIA haber. Es el gancho del manual.
    cat_raw = {r["Categoria"] for r in filas}
    med["categorias_distintas_crudas"] = len(cat_raw)
    suc_raw = {r["Sucursal"].strip().replace("\xa0", " ") for r in filas}
    med["sucursales_distintas_crudas"] = len(suc_raw)
    ven_raw = {r["Vendedor"] for r in filas}
    med["vendedores_distintos_crudos"] = len(ven_raw)

    # --- fechas: formato vs VALIDEZ (dos cosas distintas)
    formatos = set()
    invalidas: list[str] = []
    for r in filas:
        t = r["Fecha"].strip()
        if PATRON_ISO.match(t):
            formatos.add("ISO (aaaa-mm-dd)")
        elif PATRON_DMA.match(t):
            formatos.add("dd/mm/aaaa")
        elif PATRON_DMA_MMM.match(t):
            formatos.add("dd-mmm-aaaa (ej. 15-mar-2024)")
        else:
            formatos.add("centinela (texto no-fecha)")
        if not fecha_valida(t):
            invalidas.append(t)
    med["formatos_de_fecha"] = len(formatos)
    med["fechas_invalidas"] = len(invalidas)
    # Se separan dos cosas MUY distintas que un diagnostico por formato confunde:
    #  - centinelas: basura explicita (1900-01-01, SIN FECHA)
    #  - mm/dd inequivocas: fecha REAL en formato estadounidense (primer num > 12)
    med["fechas_centinela"] = sum(1 for t in invalidas if t in CENTINELAS)
    # Una fecha "A/B/aaaa" leida como dd/mm usa B como mes. Si B > 12 no puede
    # ser un mes, asi que la unica lectura valida es mm/dd (B es el dia).
    med["fechas_mm_dd_inequivocas"] = sum(
        1 for t in invalidas
        if t not in CENTINELAS and PATRON_DMA.match(t)
        and int(t.split("/")[1]) > 12
    )

    med["precios_con_coma"] = sum(1 for r in filas if "," in r[COL_PRECIO])
    med["precios_con_punto"] = len(filas) - med["precios_con_coma"]

    # Desglose del problema de separadores (manual, seccion 6b)
    PAT_ES_FMT = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")
    PAT_EN_FMT = re.compile(r"^\d+\.\d{2}$")
    med["precios_es_con_miles"] = sum(
        1 for r in filas
        if "," in r[COL_PRECIO] and "." in r[COL_PRECIO]
        and PAT_ES_FMT.match(r[COL_PRECIO].strip())
    )
    med["precios_es_simple"] = sum(
        1 for r in filas
        if "," in r[COL_PRECIO] and "." not in r[COL_PRECIO]
    )
    # Dot como separador DECIMAL = tiene punto y NO tiene coma. Es la definicion
    # semantica correcta, mas amplia que el patron estricto \d+\.\d{2}: hay 78
    # valores con UN solo decimal (ej. '5179.8'), porque el generador serializa
    # los flotantes con str() y eso descarta los ceros finales. El punto sigue
    # siendo decimal, asi que cuentan igual para el problema de locale.
    med["precios_en_punto_decimal"] = sum(
        1 for r in filas if "." in r[COL_PRECIO] and "," not in r[COL_PRECIO]
    )
    med["precios_en_punto_decimal_un_decimal"] = sum(
        1 for r in filas
        if "." in r[COL_PRECIO] and "," not in r[COL_PRECIO]
        and len(r[COL_PRECIO].strip().split(".")[1]) == 1
    )

    # Errores de conversion de fecha con locale es-ES (dd/mm/aaaa)
    med["errores_fecha_es_es"] = sum(
        1 for r in filas if not fecha_valida_es_es(r["Fecha"])
    )
    med["filas_con_nbsp"] = sum(
        1 for r in filas if "\xa0" in "".join(str(v) for v in r.values())
    )

    # --- cuantas filas incumplen la regla del total
    mal_total = 0
    for r in filas:
        try:
            cant = int(r["Cantidad"])
            precio = a_num(r[COL_PRECIO])
            d = float(r["Descuento"])
            if d > 1:
                d = d / 100
            d = min(max(d, 0.0), 1.0)
            if abs(cant * precio * (1 - d) - a_num(r[COL_TOTAL])) > 1.0:
                mal_total += 1
        except ValueError:
            mal_total += 1
    med["totales_inconsistentes"] = mal_total

    # ------------------------------------------------------------- comparacion
    print("[i] Afirmaciones del manual vs datos reales\n")
    print(f"    {'Afirmacion':<34}{'Manual':>8}{'Real':>8}   Estado")
    for clave, esperado in AFIRMACIONES.items():
        real = med.get(clave)
        if real is None:
            continue
        ok = real == esperado
        if not ok:
            fallos.append(f"{clave}: manual={esperado} real={real}")
        print(f"    {clave:<34}{esperado:>8}{real:>8}   {'OK' if ok else 'FALLA'}")

    print("\n[i] Mediciones adicionales (se citan en el manual)")
    for clave in ["categorias_distintas_crudas", "sucursales_distintas_crudas",
                  "vendedores_distintos_crudos", "fechas_invalidas",
                  "fechas_centinela", "fechas_mm_dd_inequivocas",
                  "precios_con_punto", "totales_inconsistentes"]:
        print(f"    {clave:<38}{med[clave]:>8}")

    print("\n[i] Valores crudos de fecha que NO son fechas validas del negocio,")
    print("    separando BASURA EXPLICITA de FECHAS ESTADOUNIDENSES:")
    from collections import Counter
    cent = Counter(t for t in invalidas if t in CENTINELAS)
    us = Counter(t for t in invalidas if t not in CENTINELAS)
    print(f"    Centinelas inyectados ({sum(cent.values())} filas):")
    for t, n in cent.most_common():
        print(f"      {t!r:<20}{n:>5}")
    # Todos los no-centinela son mm/dd con dia > 12: por eso son inequivocas.
    print(f"    mm/dd inequivocas ({sum(us.values())} filas) — prueba de que el "
          f"formato estadounidense EXISTE en los datos:")
    for t, n in list(us.most_common())[:6]:
        print(f"      {t!r:<20}{n:>5}")
    if len(us) > 6:
        print(f"      ... y {len(us) - 6} valores mas")

    print("\n[i] Formato de fecha -> ojo: '2025-13-45' TIENE formato ISO y es imposible")
    for f in sorted(formatos):
        print(f"    - {f}")

    if med["fechas_centinela"] == 0:
        fallos.append("no hay centinelas: revisar el dataset")
    if med["fechas_mm_dd_inequivocas"] == 0:
        fallos.append("no hay fechas mm/dd inequivocas: el manual afirma que existen")

    if fallos:
        print(f"\n[!] EL MANUAL NO COINCIDE CON LOS DATOS: {fallos}", file=sys.stderr)
        return 1
    print("\n[OK] Todas las afirmaciones del manual coinciden con los datos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
