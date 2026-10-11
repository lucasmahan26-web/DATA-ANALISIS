"""
Genera el dataset del Proyecto 1 (Excel + Power Query / retail de supermercado).

Estrategia anti-error:
  1. Se construyen filas LIMPIAS con tipos nativos.
  2. Se inyectan 12 tipos de defectos en orden controlado (el Total se recalcula al
     final, de modo que SOLO las filas de D8 queden realmente inconsistentes).
  3. Se serializa a texto EXACTAMENTE lo que se va a escribir en el CSV.
  4. Se escanea esa representacion en memoria y se RE-LEE el CSV desde el archivo.
     Los dos escaneos deben coincidir: eso valida el viaje escribir->leer.
  5. La clave de respuestas se genera con los valores MEDIDOS del archivo.

Ejecutar:  <python> scripts/generar_dataset_p1.py
"""

from __future__ import annotations

import csv
import random
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

random.seed(20240115)

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "datos"
DATOS.mkdir(exist_ok=True)

N_FILAS_LIMPIAS = 2900
FECHA_MIN = date(2023, 1, 1)
FECHA_MAX = date(2024, 12, 31)
NBSP = "\xa0"

# --------------------------------------------------------------------------
# Catalogos de negocio
# --------------------------------------------------------------------------
SUCURSALES = [
    ("SUC-01", "Central Rosario", "Litoral", "Zona Este"),
    ("SUC-02", "Sucursal Norte", "Norte", "Zona Norte"),
    ("SUC-03", "Sucursal Sur", "Sur", "Zona Sur"),
    ("SUC-04", "Mendoza Centro", "Cuyo", "Zona Oeste"),
    ("SUC-05", "Cordoba Nueva", "Centro", "Zona Centro"),
    ("SUC-06", "La Plata", "Centro", "Zona Este"),
    ("SUC-07", "Tucuman Shopping", "Norte", "Zona Norte"),
    ("SUC-08", "Bariloche", "Sur", "Zona Sur"),
]
REGION_OFICIAL = {n: r for _c, n, r, _z in SUCURSALES}

# Formas incorrectas con las que el sistema viejo escribe algunas sucursales
SUCURSAL_MAL_ESCRITA = {
    "SUC-02": ["sucursal norte", "Sucursal  Norte", "SUCURSAL NORTE"],
    "SUC-05": ["Córdoba Nueva", "Cordoba  Nueva"],
    "SUC-06": ["la plata", "LA PLATA", "La  Plata"],
    "SUC-07": ["Tucuman Sho ping", "Tucumán Shopping"],
}

CATALOGO = {
    "Almacén": [
        ("Arroz Largo Fino 1kg", 1250.0),
        ("Fideos Spaghetti 500g", 890.0),
        ("Aceite Girasol 1.5L", 3200.0),
        ("Azúcar Refinada 1kg", 1100.0),
    ],
    "Bebidas": [
        ("Gaseosa Cola 2.25L", 1850.0),
        ("Agua Mineral 500ml", 620.0),
        ("Cerveza Rubia 1L", 2100.0),
        ("Jugo de Naranja 1L", 1450.0),
    ],
    "Lácteos": [
        ("Leche Entera 1L", 1180.0),
        ("Yogur Bebible 200g", 750.0),
        ("Queso Cremoso kg", 5600.0),
        ("Manteca 200g", 1900.0),
    ],
    "Limpieza": [
        ("Detergente 750ml", 1350.0),
        ("Lavandina 1L", 780.0),
        ("Jabón en Polvo 3x", 4200.0),
        ("Rollo de Cocina 3u", 1100.0),
    ],
    "Carnes": [
        ("Asado de Tira kg", 8900.0),
        ("Milanesa de Nalga kg", 7400.0),
        ("Pollo Entero kg", 3900.0),
        ("Bondiola de Cerdo kg", 6800.0),
    ],
    "Panadería": [
        ("Pan Francés kg", 1600.0),
        ("Facturas 6u", 2100.0),
        ("Budín Marmolado", 2400.0),
        ("Galletitas Surtidas 300g", 980.0),
    ],
    "Frutas y Verduras": [
        ("Manzana Red Delicious kg", 1750.0),
        ("Banana Ecuador kg", 1500.0),
        ("Papa Negra kg", 950.0),
        ("Tomate Perita kg", 2100.0),
    ],
    "Congelados": [
        ("Hamburguesas 4u", 3400.0),
        ("Arvejas 500g", 1250.0),
        ("Helado 1L", 4300.0),
        ("Papas Fritas 1kg", 2800.0),
    ],
}

VENDEDORES = [
    "Ana Giménez", "Bruno Salas", "Carla Duarte", "Diego Ferreyra",
    "Elena Ruiz", "Facundo Paz", "Gabriela Sosa", "Hernán Ledesma",
    "Irene Molina", "Javier Ocampo", "Karina Vidal", "Luis Benítez",
]
CLIENTES = [
    "Consumidor Final", "Kiosco El Sol", "Restaurant Don Pedro", "Hotel Costanera",
    "Colegio San Martín", "Panadería La Espiga", "Oficina Contable Ríos", "Bar La Esquina",
    "Gimnasio Fitness Plus", "Farmacia Del Pueblo", "Estudio Jurídico Vega", "Cafetería Aroma",
]
METODOS_PAGO = ["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia", "QR"]
CANALES = ["Local", "Online", "Teléfono"]

ENCABEZADOS = [
    "ID_Pedido", "Fecha", "Cliente", "Sucursal", "Region", "Vendedor",
    "Categoria", "Producto", "Cantidad", "Precio_Unitario ($)", "Descuento",
    "Total ($)", "Metodo_Pago", "Canal",
]

MESES_ABREV = ["ene", "feb", "mar", "abr", "may", "jun",
               "jul", "ago", "sep", "oct", "nov", "dic"]

VALORES_FECHA_INVALIDA = ["1900-01-01", "2025-13-45", "31/02/2024", "0000-00-00", "SIN FECHA"]
NULOS = ["", "N/A", "-", "SIN DATO", "(en blanco)", "  "]


# --------------------------------------------------------------------------
# Helpers de formato
# --------------------------------------------------------------------------
def formatear_numero_ar(valor: float) -> str:
    """1234.56 -> '1.234,56'  (miles con punto, decimales con coma)."""
    return f"{valor:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def formatear_numero_plano(valor: float) -> str:
    return f"{valor:.2f}"


def formatear_fecha_europea(f: date) -> str:
    return f"{f.day:02d}/{f.month:02d}/{f.year}"


def formatear_fecha_con_mes(f: date) -> str:
    return f"{f.day:02d}-{MESES_ABREV[f.month - 1]}-{f.year}"


def formatear_fecha_eeuu(f: date) -> str:
    return f"{f.month:02d}/{f.day:02d}/{f.year}"


def a_num(t: str) -> float:
    """Parsea tanto '1.234,56' como '1234.56'."""
    t = t.strip()
    if "," in t:
        return float(t.replace(".", "").replace(",", "."))
    return float(t)


def descuento_efectivo(d: float) -> float:
    """Interpretacion razonable de un descuento mal cargado (15 -> 0,15)."""
    if d > 1:
        d = d / 100
    return min(max(d, 0.0), 1.0)


def norm_ws(s: str) -> str:
    """Colapsa espacios (incluido NBSP) y recorta."""
    return " ".join(s.replace(NBSP, " ").split())


def norm_total(s: str) -> str:
    """Normaliza para comparar categorias: sin espacios, sin mayusculas, sin tildes."""
    s = norm_ws(s).casefold()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


OFICIALES_NORM = {norm_total(c): c for c in CATALOGO}


# --------------------------------------------------------------------------
# Paso 1: filas limpias
# --------------------------------------------------------------------------
filas: list[dict] = []
for i in range(N_FILAS_LIMPIAS):
    cod_suc, nombre, region, _zona = random.choice(SUCURSALES)
    categoria = random.choice(list(CATALOGO.keys()))
    producto, precio_base = random.choice(CATALOGO[categoria])

    fecha = FECHA_MIN + timedelta(days=random.randint(0, (FECHA_MAX - FECHA_MIN).days))
    factor = 1.0 + 0.35 * ((fecha - FECHA_MIN).days / (FECHA_MAX - FECHA_MIN).days)
    precio = round(precio_base * factor * random.uniform(0.95, 1.05), 2)

    cantidad = random.choices(
        [1, 2, 3, 4, 6, 8, 12, 18, 24], weights=[30, 22, 15, 10, 8, 6, 4, 3, 2]
    )[0]
    descuento = random.choices([0.0, 0.05, 0.10, 0.15, 0.20, 0.25],
                               weights=[55, 12, 12, 10, 8, 3])[0]

    filas.append({
        "ID_Pedido": f"PED-{i + 1:06d}",
        "Fecha": fecha,
        "Cliente": random.choice(CLIENTES),
        "Sucursal": nombre,
        "cod_suc": cod_suc,
        "Region": region,
        "Vendedor": random.choice(VENDEDORES),
        "Categoria": categoria,
        "Producto": producto,
        "Cantidad": cantidad,
        "Precio": precio,
        "Descuento": descuento,
        "Metodo_Pago": random.choice(METODOS_PAGO),
        "Canal": random.choice(CANALES),
    })

print(f"[1] Filas limpias generadas: {N_FILAS_LIMPIAS}")

# --------------------------------------------------------------------------
# Paso 2: inyeccion de defectos (orden controlado)
# --------------------------------------------------------------------------
base = list(range(N_FILAS_LIMPIAS))

# --- D2: Categoria con mayusculas / tildes / doble espacio -----------------
# D2 es SOLO mayusculas/minusculas y tildes. Los espacios son D10 (responsabilidad
# separada), para que los dos conteos no se solapen y el ejercicio sea inequivoco.
idx_d2: list[int] = []
for i in random.sample(base, 200):
    cat = filas[i]["Categoria"]
    variante = random.choice(["upper", "lower", "sin_tilde"])
    if variante == "upper":
        nuevo = cat.upper()
    elif variante == "lower":
        nuevo = cat.lower()
    else:
        nuevo = (cat.replace("á", "a").replace("é", "e")
                 .replace("í", "i").replace("ó", "o").replace("ú", "u"))
    if nuevo == cat:
        continue  # variante sin efecto: no es un defecto, no lo contamos
    filas[i]["Categoria"] = nuevo
    idx_d2.append(i)
    if len(idx_d2) == 140:
        break
print(f"[2] D2  categorias con case/tildes inconsistentes: {len(idx_d2)}")

# --- D3: Fecha guardada como texto en varios formatos ----------------------
# OJO: la variante "eeuu" (mm/dd/aaaa) introduce un problema mas sutil que el
# formato: AMBIGUEDAD. "03/04/2024" es 3 de abril o 4 de marzo segun quien lo
# lea, y Power Query va a elegir una interpretacion sin avisar. Se cuentan por
# separado las que son INEQUIVOCAMENTE mm/dd (primer numero > 12), porque esas
# son la evidencia de que el formato existe en los datos.
idx_d3 = random.sample(base, 900)
formato_d3: dict[str, int] = {}
us_inequivocas = 0
for i in idx_d3:
    f = filas[i]["Fecha"]
    formato = random.choices(["iso", "europea", "mes_abrev", "eeuu"], weights=[55, 25, 12, 8])[0]
    formato_d3[formato] = formato_d3.get(formato, 0) + 1
    if formato == "iso":
        filas[i]["Fecha"] = f.isoformat()
    elif formato == "europea":
        filas[i]["Fecha"] = formatear_fecha_europea(f)
    elif formato == "mes_abrev":
        filas[i]["Fecha"] = formatear_fecha_con_mes(f)
    else:
        filas[i]["Fecha"] = formatear_fecha_eeuu(f)
        # La fecha esta escrita como mm/dd. Leida como dd/mm, el SEGUNDO numero
        # hace de mes. Si ese segundo numero es > 12, no puede ser un mes: la
        # fecha es inequivocamente estadounidense. Esa es la evidencia de que
        # el formato existe en los datos (y de que las ambiguas hay que revisarlas).
        if f.day > 12:
            us_inequivocas += 1
print(f"[2] D3  fechas en 4 formatos de texto distintos: {len(idx_d3)} "
      f"({formato_d3.get('iso', 0)} quedan ISO, {formato_d3.get('europea', 0)} dd/mm, "
      f"{formato_d3.get('mes_abrev', 0)} dd-mmm, {formato_d3.get('eeuu', 0)} mm/dd)")
print(f"        de las mm/dd, {us_inequivocas} son inequivocamente estadounidenses "
      f"(el dia, segundo numero, es > 12) y el resto son ambiguas")

# --- D4: Fechas invalidas o centinela -------------------------------------
idx_d4 = random.sample([x for x in base if x not in idx_d3], 14)
for i in idx_d4:
    filas[i]["Fecha"] = random.choice(VALORES_FECHA_INVALIDA)
print(f"[2] D4  fechas invalidas / centinela: {len(idx_d4)}")

# --- D5: Nulos encubiertos como texto ------------------------------------
idx_d5a = random.sample(base, 95)
for i in idx_d5a:
    filas[i]["Vendedor"] = random.choice(NULOS)
idx_d5b = random.sample([x for x in base if x not in idx_d5a], 45)
for i in idx_d5b:
    filas[i]["Cliente"] = random.choice(NULOS)
print(f"[2] D5  nulos encubiertos (Cliente/Vendedor): {len(idx_d5a) + len(idx_d5b)}")

# --- D6: Cantidades negativas (devoluciones no marcadas) ------------------
idx_d6 = random.sample(base, 55)
for i in idx_d6:
    filas[i]["Cantidad"] = -abs(filas[i]["Cantidad"])
print(f"[2] D6  cantidades negativas: {len(idx_d6)}")

# --- D7: Mezcla de formato numerico --------------------------------------
idx_d7 = random.sample(base, int(N_FILAS_LIMPIAS * 0.70))
for i in idx_d7:
    filas[i]["Precio"] = formatear_numero_ar(float(filas[i]["Precio"]))
print(f"[2] D7  precios en formato AR '1.234,56': {len(idx_d7)}")

# --- D9: Descuento fuera de rango ----------------------------------------
idx_d9 = random.sample(base, 48)
for i in idx_d9:
    # Valores SIN ambiguedad interpretativa:
    #  - > 1 y claramente porcentaje (15, 20, 25, 30) -> dividir por 100
    #  - negativos, claramente invalidos (-0.10, -5)
    # Se excluyen 100 (dejaria Total = 0 y haria indetectable un D8 sobre la
    # misma fila) y 1.5 (ambiguo: 150% o typo de 0,15), para que la consigna
    # "el Total cuadra en todas las filas" tenga una unica respuesta correcta.
    filas[i]["Descuento"] = random.choice([15, 20, 25, 30, -0.10, -5])
print(f"[2] D9  descuentos fuera del rango 0-1: {len(idx_d9)}")

# --- D12: Precios atipicos por error de tipeo (x100) ---------------------
idx_d12 = random.sample(base, 16)
for i in idx_d12:
    p = a_num(str(filas[i]["Precio"]))
    nuevo = round(p * 100, 2)
    filas[i]["Precio"] = formatear_numero_ar(nuevo) if i in idx_d7 else formatear_numero_plano(nuevo)
print(f"[2] D12 precios atipicos (x100): {len(idx_d12)}")

# --- D11: Region incorrecta o sucursal mal escrita -----------------------
idx_d11 = random.sample(base, 160)
idx_d11_region: list[int] = []
idx_d11_sucursal: list[int] = []
for i in idx_d11:
    cod = filas[i]["cod_suc"]
    if cod in SUCURSAL_MAL_ESCRITA and len(idx_d11_sucursal) < 90:
        filas[i]["Sucursal"] = random.choice(SUCURSAL_MAL_ESCRITA[cod])
        idx_d11_sucursal.append(i)
    else:
        otras = [r for _c, _n, r, _z in SUCURSALES if r != filas[i]["Region"]]
        filas[i]["Region"] = random.choice(otras)
        idx_d11_region.append(i)
print(f"[2] D11 region incorrecta: {len(idx_d11_region)} | "
      f"sucursal fuera de catalogo: {len(idx_d11_sucursal)}")

# --- D10: Espacios extra y NBSP (sin pisar Sucursal: eso es D11) ----------
idx_d10 = random.sample(base, 210)
conteo_d10 = 0
for i in idx_d10:
    candidatos = ["Vendedor", "Producto", "Categoria"]
    if i in idx_d5a:
        candidatos.remove("Vendedor")
    if i in idx_d2:
        candidatos.remove("Categoria")
    if not candidatos:
        continue
    campo = random.choice(candidatos)
    valor = str(filas[i][campo])
    estilos = ["lead", "trail", "nbsp", "doble"]
    if " " in valor:  # el espacio interno tambien es un defecto de limpieza
        estilos.append("interna")
    estilo = random.choice(estilos)
    if estilo == "lead":
        valor = " " + valor
    elif estilo == "trail":
        valor = valor + "  "
    elif estilo == "nbsp":
        valor = valor.replace(" ", NBSP, 1)
    elif estilo == "interna":
        valor = valor.replace(" ", "  ", 1)
    else:
        valor = " " + valor + " "
    filas[i][campo] = valor
    conteo_d10 += 1
print(f"[2] D10 espacios extra / NBSP: {conteo_d10}")

# --- Recalculo del Total (ultimo paso antes de corromper D8) -------------
# Se recalcula para TODAS las filas, de modo que la unica causa de
# inconsistencia sea D8. La cantidad negativa genera un total negativo real.
for f in filas:
    precio = a_num(str(f["Precio"]))
    f["Total"] = round(f["Cantidad"] * precio * (1 - descuento_efectivo(f["Descuento"])), 2)

# --- D8: Total que no cuadra --------------------------------------------
idx_d8 = random.sample(base, 120)
for i in idx_d8:
    filas[i]["Total"] = round(filas[i]["Total"] * random.choice([0.87, 1.13, 0.72, 1.25]), 2)
print(f"[2] D8  totales inconsistentes: {len(idx_d8)}")

# --- D1: Duplicados exactos (ULTIMO: se clonan filas ya terminadas) ------
idx_d1 = random.sample(base, 35)
for i in idx_d1:
    filas.append(dict(filas[i]))
print(f"[2] D1  duplicados exactos de fila: {len(idx_d1)}")

# --------------------------------------------------------------------------
# Paso 3: serializar a texto (una sola fuente de verdad para CSV y escaneo)
# --------------------------------------------------------------------------
def serializar(f: dict) -> list[str]:
    fecha = f["Fecha"]
    return [
        f["ID_Pedido"],
        fecha.isoformat() if isinstance(fecha, date) else str(fecha),
        str(f["Cliente"]),
        str(f["Sucursal"]),
        str(f["Region"]),
        str(f["Vendedor"]),
        str(f["Categoria"]),
        str(f["Producto"]),
        str(f["Cantidad"]),
        str(f["Precio"]),
        str(f["Descuento"]),
        formatear_numero_plano(float(f["Total"])),
        str(f["Metodo_Pago"]),
        str(f["Canal"]),
    ]


registros_texto = [serializar(f) for f in filas]

RUTA_CSV = DATOS / "P1_ventas_crudo.csv"
with RUTA_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(ENCABEZADOS)
    w.writerows(registros_texto)
print(f"\n[3] CSV escrito: {RUTA_CSV} ({len(registros_texto)} filas + encabezado)")

RUTA_CAT = DATOS / "P1_catalogo_sucursales.csv"
with RUTA_CAT.open("w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["Codigo_Sucursal", "Sucursal", "Region_Oficial", "Zona_Comercial"])
    for cod, nombre, region, zona in SUCURSALES:
        w.writerow([cod, nombre, region, zona])
print(f"[3] Catalogo de referencia escrito: {RUTA_CAT} ({len(SUCURSALES)} filas)")

# --------------------------------------------------------------------------
# Paso 4: escaneo de defectos, aplicado a memoria Y al archivo
# --------------------------------------------------------------------------
def escanear(registros: list[dict]) -> dict[str, int]:
    med = {k: 0 for k in
           ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
            "D9", "D10", "D11a", "D11b", "D12"]}

    # D1: filas exactamente iguales (las sobrantes)
    vistos: set[tuple] = set()
    for r in registros:
        clave = tuple(r[c] for c in ENCABEZADOS)
        if clave in vistos:
            med["D1"] += 1
        else:
            vistos.add(clave)

    for r in registros:
        cat_raw = r["Categoria"]
        cat_ws = norm_ws(cat_raw)

        # D10: espacios al inicio/fin o NBSP en cualquier columna de texto
        cols_texto = ["Cliente", "Sucursal", "Region", "Vendedor",
                      "Categoria", "Producto", "Metodo_Pago", "Canal"]
        if any(r[c] != norm_ws(r[c]) or NBSP in r[c] for c in cols_texto):
            med["D10"] += 1

        # D2: categoria que normaliza a una oficial pero no es la forma oficial
        norm = norm_total(cat_raw)
        if (norm in OFICIALES_NORM
                and cat_raw != OFICIALES_NORM[norm]
                and cat_ws == cat_raw):
            med["D2"] += 1

        # D3 / D4: fecha
        fe = r["Fecha"].strip()
        iso = len(fe) == 10 and fe[4:5] == "-" and fe[7:8] == "-"
        if fe in VALORES_FECHA_INVALIDA:
            med["D4"] += 1
        elif not iso:
            med["D3"] += 1

        # D5: nulos encubiertos
        if (r["Cliente"].strip() in {"", "N/A", "-", "SIN DATO", "(en blanco)"}
                or r["Vendedor"].strip() in {"", "N/A", "-", "SIN DATO", "(en blanco)"}):
            med["D5"] += 1

        # D6: cantidad negativa
        if int(r["Cantidad"]) < 0:
            med["D6"] += 1

        # D7: precio con coma decimal
        if "," in r["Precio_Unitario ($)"]:
            med["D7"] += 1

        # D9: descuento fuera de rango
        d = float(r["Descuento"])
        if d < 0 or d > 1:
            med["D9"] += 1

        # D8: total que no cuadra (cantidad CON signo, descuento interpretado)
        esperado = int(r["Cantidad"]) * a_num(r["Precio_Unitario ($)"]) * (1 - descuento_efectivo(d))
        if abs(esperado - a_num(r["Total ($)"])) > 1.0:
            med["D8"] += 1

        # D11: region vs catalogo / sucursal fuera de catalogo
        suc = norm_ws(r["Sucursal"])
        if suc in REGION_OFICIAL:
            if norm_ws(r["Region"]) != REGION_OFICIAL[suc]:
                med["D11a"] += 1
        else:
            med["D11b"] += 1

        # D12: precio atipico
        max_razonable = max(p for lst in CATALOGO.values() for _n, p in lst) * 1.4
        if a_num(r["Precio_Unitario ($)"]) > max_razonable * 2:
            med["D12"] += 1

    return med


with RUTA_CSV.open("r", newline="", encoding="utf-8-sig") as fh:
    crudos = list(csv.DictReader(fh))
en_archivo = escanear(crudos)

NOMBRES = {
    "D1": "Duplicados exactos de fila",
    "D2": "Categoria con mayusculas / sin tildes",
    "D3": "Fecha como texto en formato no ISO",
    "D4": "Fecha invalida o centinela",
    "D5": "Nulo encubierto como texto (Cliente / Vendedor)",
    "D6": "Cantidad negativa (devolucion no marcada)",
    "D7": "Precio con coma decimal (formato AR)",
    "D8": "Total que no cuadra con Cant * Precio * (1 - Desc)",
    "D9": "Descuento fuera del rango 0-1",
    "D10": "Espacios sobrantes (inicio/fin/internos) o NBSP",
    "D11a": "Region que no coincide con el catalogo",
    "D11b": "Sucursal irreconocible incluso normalizando espacios",
    "D12": "Precio atipico (error de tipeo x100)",
}
# Referencia con sentido: se escanean por separado las 2900 filas base y las
# 2935 del archivo. La diferencia debe ser el efecto de los clones de D1:
# toda fila clonada hereda los defectos de su origen y se cuenta dos veces.
todos_dicts = [dict(zip(ENCABEZADOS, fila)) for fila in registros_texto]
base_dicts = todos_dicts[:N_FILAS_LIMPIAS]
scan_total = escanear(todos_dicts)
scan_base = escanear(base_dicts)

print("\n[4] VERIFICACION")
print(f"    Filas en el archivo         : {len(crudos)}")
print(f"    Filas esperadas             : {N_FILAS_LIMPIAS + len(idx_d1)}")
print(f"\n    {'Cod':<6}{'Base':>7}{'Archivo':>9}{'Clones':>8}   Defecto")
fallos: list[str] = []
for cod in NOMBRES:
    clones = scan_total[cod] - scan_base[cod]
    if scan_total[cod] != en_archivo[cod]:
        fallos.append(f"{cod}:MEM!=ARCH")
        nota = "  <-- MEMORIA != ARCHIVO"
    elif not (0 <= clones <= len(idx_d1)):
        fallos.append(f"{cod}:CLONES={clones}")
        nota = f"  <-- clones fuera de rango (max {len(idx_d1)})"
    else:
        nota = ""
    print(f"    {cod:<6}{scan_base[cod]:>7}{en_archivo[cod]:>9}"
          f"{clones:>8}   {NOMBRES[cod]}{nota}")

# Invariante de coherencia: el total de cada defecto debe repartirse
# entre "filas base afectadas" y "clones de filas afectadas".
if len(crudos) != N_FILAS_LIMPIAS + len(idx_d1):
    fallos.append(f"FILAS({len(crudos)})")
if en_archivo["D1"] != len(idx_d1):
    fallos.append("D1-INDETECTABLE")

# --------------------------------------------------------------------------
# Paso 5: clave de respuestas con los valores MEDIDOS
# --------------------------------------------------------------------------
filas_unicas = len(crudos) - en_archivo["D1"]
TECNICAS = {
    "D1": "Inicio > Quitar filas > **Quitar duplicados**",
    "D2": "Transformar > Formato > **Capitalizar cada palabra** + Reemplazar valores + Recortar",
    "D3": "Tipo de dato > Fecha **con configuración regional** (dd/mm/aaaa); para `15-mar-2024` usar **Columna de ejemplo**",
    "D4": "**Filtrar** los centinelas antes de convertir el tipo; si no, la consulta entera queda en Error",
    "D5": "Reemplazar valores (`N/A`, `-`, `SIN DATO`, `(en blanco)`) por **null** + Quitar filas vacías",
    "D6": "**Decisión de negocio**: son devoluciones. Separarlas en otra consulta y calcular venta neta, no borrarlas",
    "D7": "Tipo de dato > Número decimal **con configuración regional** (coma decimal) + Reemplazar valores",
    "D8": "**Columna personalizada** recalculando `Cantidad * Precio * (1 - Descuento)`. Nunca confiar en el total del sistema",
    "D9": "Filtrar rango válido 0–1 + convertir los valores >1 (`15`, `20`, `25`, `30`) a decimal dividiendo por 100, y decidir qué hacer con los negativos (`-0,10`, `-5`)",
    "D10": "Transformar > Formato > **Recortar** + **Limpiar** + reemplazar el NBSP y los espacios internos dobles. Invisible, pero rompe el Merge",
    "D11a": "**Merge** contra `P1_catalogo_sucursales.csv` y quedarse con `Region_Oficial`",
    "D11b": "Merge con **coincidencia aproximada** o tabla de equivalencias manual (`sucursal norte` vs `Sucursal Norte`)",
    "D12": "Comparar contra el precio máximo del catálogo, marcar atípicos y decidir si excluir o corregir",
}

lineas = [
    "# CLAVE DE RESPUESTAS — NO ABRIR HASTA TERMINAR TU LIMPIEZA",
    "",
    "> Si lo leés antes, el ejercicio no sirve. Usalo solo para autoevaluarte.",
    "",
    "## Números de control",
    "",
    f"- Filas totales en `P1_ventas_crudo.csv`: **{len(crudos)}**",
    f"- Filas duplicadas a eliminar: **{en_archivo['D1']}**",
    f"- Filas únicas reales: **{filas_unicas}**",
    "",
    "Los conteos son por **fila del archivo**: una misma fila puede tener varios defectos,",
    "así que la suma de la columna no da el total de filas.",
    "",
    f"Ojo: las **{en_archivo['D1']} filas duplicadas** arrastran los defectos de su fila original. "
    "Si una fila con precio atípico fue duplicada, ese defecto aparece dos veces. Por eso los "
    "conteos son de *filas del archivo* y no de *casos distintos*.",
    "",
    "---",
    "",
    "## Defectos inyectados y técnica que los resuelve",
    "",
    "| Cod | Defecto | Filas | Técnica esperada en Power Query |",
    "|---|---|---|---|",
]
for cod in NOMBRES:
    lineas.append(f"| {cod} | {NOMBRES[cod]} | {en_archivo[cod]} | {TECNICAS[cod]} |")

lineas += [
    "",
    f"**Sobre D3:** las {len(crudos)} filas tienen la fecha como texto. De esas, "
    f"**{en_archivo['D3']}** usan un formato distinto al ISO. Pero hay un problema más "
    "sutil que el formato: **la ambigüedad**. El dataset mezcla `dd/mm/aaaa` con "
    f"`mm/dd/aaaa`, y de las fechas con barras, **{us_inequivocas}** son inequívocamente "
    "estadounidenses (el día aparece en la posición del mes y es mayor a 12).",
    "",
    "> **Esto es lo más difícil del proyecto y casi nadie lo detecta.** Una fecha como "
    "`03/04/2024` es válida en los dos formatos: puede ser 3 de abril o 4 de marzo. "
    "Power Query **va a elegir una interpretación según la configuración regional y no "
    "te va a avisar**. Si elegís mal, tenés fechas corridas hasta 11 meses y todos tus "
    "análisis mensuales quedan mal, sin ningún error visible.",
    ">",
    "> **Cómo se detecta:** buscá fechas donde el primer número sea mayor a 12. Si "
    "existen, el formato estadounidense está presente, y entonces **las ambiguas también "
    "hay que revisarlas**. No hay forma de resolverlas automáticamente: hay que decidir "
    "con criterio y documentarlo.",
    "",
    "---",
    "",
    "## Pruebas objetivas: tu limpieza está bien si...",
    "",
    f"- [ ] Te quedan **{filas_unicas}** filas (o menos, si además separaste las devoluciones; anotá por qué)",
    "- [ ] `Fecha` es tipo **Fecha**. Ninguna fecha fuera de 2023–2024 y ningún Error en la columna",
    "- [ ] `Categoria` tiene exactamente **8 valores únicos**: "
    + ", ".join(f"`{c}`" for c in CATALOGO),
    "- [ ] `Precio_Unitario` y `Total` son tipo **Número decimal** (ninguna coma visible)",
    "- [ ] `Descuento` está entre **0 y 1** (ningún valor tipo `15` o `-5`)",
    "- [ ] `Cliente` y `Vendedor` sin `N/A`, `-` ni `SIN DATO`",
    f"- [ ] **0** sucursales fuera del catálogo (había {en_archivo['D11b']}) y **0** regiones mal asignadas (había {en_archivo['D11a']})",
    f"- [ ] `Total` recalculado cuadra en **todas** las filas (había {en_archivo['D8']} que no cuadraban)",
    "- [ ] Ninguna celda de texto empieza o termina con espacio, y no queda ningún NBSP",
    f"- [ ] Los **{en_archivo['D12']}** precios atípicos están detectados y decidiste qué hacer con ellos",
    "",
    "---",
    "",
    "## Preguntas de negocio (estas NO tienen una única respuesta correcta)",
    "",
    f"1. Las **{en_archivo['D6']}** filas con cantidad negativa: ¿son devoluciones, errores de carga o notas de crédito? "
    "¿Cómo lo averiguarías sin poder preguntarle a nadie?",
    "2. ¿El `Total` del sistema o tu recálculo es la fuente de verdad? ¿Por qué?",
    f"3. Los **{en_archivo['D12']}** precios atípicos: ¿los excluís, los corregís (dividiendo por 100) o los dejás? "
    "Cada opción cambia el total facturado.",
    f"4. Las **{en_archivo['D4']}** filas con fecha inválida: al filtrarlas, ¿estás perdiendo ventas reales?",
    f"5. Las **{en_archivo['D9']}** filas con descuento fuera de rango: si un descuento de `15` en realidad era 15%, "
    "¿aceptás ese total o lo recalculás?",
    "",
    "> Estas 5 preguntas son exactamente el tipo de cosa que te van a preguntar en una entrevista. "
    "Escribí tu respuesta en el README del proyecto.",
    "",
    "---",
    "",
    "## Archivos del dataset",
    "",
    "| Archivo | Qué es |",
    "|---|---|",
    "| `P1_ventas_crudo.csv` | Tabla de ventas sucia (fuente principal, todo como texto) |",
    "| `P1_catalogo_sucursales.csv` | Tabla de referencia limpia, para practicar **Merge** |",
    "| `P1_DEFECTOS_clave_NO_ABRIR.md` | Este archivo |",
    "",
]
RUTA_CLAVE = DATOS / "P1_DEFECTOS_clave_NO_ABRIR.md"
RUTA_CLAVE.write_text("\n".join(lineas), encoding="utf-8")
print(f"\n[5] Clave de respuestas escrita: {RUTA_CLAVE}")

if fallos:
    print(f"\n[!] ATENCION: revisar {fallos}", file=sys.stderr)
    sys.exit(1)
print("\n[OK] Memoria == archivo en los 13 conteos, el total de filas es el esperado "
      f"y los clones de cada defecto caen dentro de 0..{len(idx_d1)}.")
