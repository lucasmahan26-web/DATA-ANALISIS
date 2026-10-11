"""
Genera el dataset del Proyecto 2 (SQL / PostgreSQL) - modelo relacional de 7 tablas
para la misma cadena de supermercados del Proyecto 1.

Diferencias deliberadas con P1:
  - P1 ensena FORMATO (fechas como texto, comas decimales, NBSP).
  - P2 ensena INTEGRIDAD REFERENCIAL y VALIDEZ (claves huerfanas, PK duplicadas,
    nulos en FK, importes inconsistentes, fechas imposibles).
  - Fechas en ISO y numeros con punto decimal: en SQL la suciedad debe estar en el
    MODELO, no en el formato, para que el foco sea el JOIN y no el parseo.
  - CSV en UTF-8 SIN BOM, porque el BOM rompe el COPY de PostgreSQL.

Verificacion (misma disciplina que P1):
  1. Se construye limpio. 2. Se inyectan defectos tipificados.
  3. Se serializa. 4. Se escanea en memoria y se re-lee del disco.
  5. Los dos escaneos deben coincidir exactamente.

Ejecutar:  <python> scripts/generar_dataset_p2.py
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

random.seed(20240401)

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "datos" / "p2"
SALIDA.mkdir(parents=True, exist_ok=True)

N_PEDIDOS = 45000
LINEAS_POR_PEDIDO = [1, 1, 2, 2, 2, 3, 3, 4, 5, 6]
FECHA_MIN = date(2023, 1, 1)
FECHA_MAX = date(2024, 12, 31)

# --------------------------------------------------------------------------
# Dimensiones limpias
# --------------------------------------------------------------------------
CATEGORIAS = [
    (1, "Almacén", "Secos"),
    (2, "Bebidas", "Bebidas"),
    (3, "Lácteos", "Frescos"),
    (4, "Limpieza", "No alimentos"),
    (5, "Carnes", "Frescos"),
    (6, "Panadería", "Frescos"),
    (7, "Frutas y Verduras", "Frescos"),
    (8, "Congelados", "Congelados"),
]

PRODUCTOS_BASE = {
    1: ["Arroz Largo Fino 1kg", "Fideos Spaghetti 500g", "Aceite Girasol 1.5L",
        "Azúcar Refinada 1kg", "Harina 000 1kg", "Yerba Mate 1kg", "Lentejas 500g",
        "Puré de Tomate 520g"],
    2: ["Gaseosa Cola 2.25L", "Agua Mineral 500ml", "Cerveza Rubia 1L",
        "Jugo de Naranja 1L", "Vino Tinto Reserva", "Fernet 750ml",
        "Gaseosa Limón 2.25L", "Agua Saborizada 1.5L"],
    3: ["Leche Entera 1L", "Yogur Bebible 200g", "Queso Cremoso kg",
        "Manteca 200g", "Crema de Leche 200ml", "Dulce de Leche 400g",
        "Queso Rallado 150g", "Leche Descremada 1L"],
    4: ["Detergente 750ml", "Lavandina 1L", "Jabón en Polvo 3x",
        "Rollo de Cocina 3u", "Limpiador Pisos 900ml", "Suavizante 900ml",
        "Esponja Multiuso 3u", "Bolsas Residuo 30u"],
    5: ["Asado de Tira kg", "Milanesa de Nalga kg", "Pollo Entero kg",
        "Bondiola de Cerdo kg", "Carne Picada kg", "Chorizo Parrillero kg"],
    6: ["Pan Francés kg", "Facturas 6u", "Budín Marmolado", "Galletitas Surtidas 300g",
        "Pan Lactal 500g", "Alfajor Triple 3u"],
    7: ["Manzana Red Delicious kg", "Banana Ecuador kg", "Papa Negra kg",
        "Tomate Perita kg", "Cebolla kg", "Zanahoria kg", "Naranja kg"],
    8: ["Hamburguesas 4u", "Arvejas 500g", "Helado 1L", "Papas Fritas 1kg",
        "Empanadas 6u", "Pizza Congelada"],
}

PRECIO_BASE_CAT = {1: 1200.0, 2: 1700.0, 3: 2100.0, 4: 1400.0,
                   5: 6500.0, 6: 1900.0, 7: 1500.0, 8: 3100.0}

SUCURSALES = [
    (1, "Central Rosario", "Litoral", "Santa Fe", "Zona Este", "2015-03-12"),
    (2, "Sucursal Norte", "Norte", "Salta", "Zona Norte", "2018-07-01"),
    (3, "Sucursal Sur", "Sur", "Chubut", "Zona Sur", "2019-11-20"),
    (4, "Mendoza Centro", "Cuyo", "Mendoza", "Zona Oeste", "2016-05-08"),
    (5, "Cordoba Nueva", "Centro", "Córdoba", "Zona Centro", "2014-09-30"),
    (6, "La Plata", "Centro", "Buenos Aires", "Zona Este", "2020-02-14"),
    (7, "Tucuman Shopping", "Norte", "Tucumán", "Zona Norte", "2017-08-22"),
    (8, "Bariloche", "Sur", "Río Negro", "Zona Sur", "2021-01-05"),
    (9, "Salta Capital", "Norte", "Salta", "Zona Norte", "2013-06-18"),
    (10, "Mar del Plata", "Centro", "Buenos Aires", "Zona Este", "2019-04-11"),
    (11, "Santa Fe Centro", "Litoral", "Santa Fe", "Zona Este", "2016-10-02"),
    (12, "Neuquen Este", "Sur", "Neuquén", "Zona Sur", "2022-03-07"),
]

NOMBRES = [
    "Ana", "Bruno", "Carla", "Diego", "Elena", "Facundo", "Gabriela", "Hernán",
    "Irene", "Javier", "Karina", "Luis", "Marina", "Nicolás", "Olga", "Pablo",
    "Quintín", "Romina", "Sergio", "Tamara", "Ulises", "Valeria", "Walter", "Ximena",
]
APELLIDOS = [
    "Giménez", "Salas", "Duarte", "Ferreyra", "Ruiz", "Paz", "Sosa", "Ledesma",
    "Molina", "Ocampo", "Vidal", "Benítez", "Acosta", "Bravo", "Cabrera", "Díaz",
]
TURNOS = ["Mañana", "Tarde", "Noche"]
TIPOS_CLIENTE = ["Consumidor Final", "Mayorista", "Empresa", "Corporativo"]
MEDIOS_PAGO = [
    (1, "Efectivo"), (2, "Tarjeta de Crédito"), (3, "Tarjeta de Débito"),
    (4, "Transferencia"), (5, "QR / Billetera Virtual"),
]
CIUDADES = [
    ("Rosario", "Santa Fe"), ("Salta", "Salta"), ("Rawson", "Chubut"),
    ("Mendoza", "Mendoza"), ("Córdoba", "Córdoba"), ("La Plata", "Buenos Aires"),
    ("San Miguel de Tucumán", "Tucumán"), ("Bariloche", "Río Negro"),
    ("Mar del Plata", "Buenos Aires"), ("Neuquén", "Neuquén"),
    ("Santa Fe", "Santa Fe"), ("Rafaela", "Santa Fe"),
]
PREFIJOS_CLIENTE = ["Supermercado", "Kiosco", "Restaurant", "Hotel", "Colegio",
                    "Farmacia", "Bar", "Gimnasio", "Panadería", "Estudio",
                    "Cafetería", "Rotisería", "Catering", "Distribuidora"]
NOMBRES_COMERCIALES = ["El Sol", "Don Pedro", "Costanera", "San Martín", "La Espiga",
                       "Ríos", "La Esquina", "Fitness Plus", "Del Pueblo", "Vega",
                       "Aroma", "Los Andes", "Del Centro", "Norte Grande"]

# --------------------------------------------------------------------------
# Paso 1: dimensiones limpias
# --------------------------------------------------------------------------
categorias = [{"id_categoria": c, "nombre_categoria": n, "departamento": d}
              for c, n, d in CATEGORIAS]

productos: list[dict] = []
pid = 1
for id_cat, nombres in PRODUCTOS_BASE.items():
    for nombre in nombres:
        base = PRECIO_BASE_CAT[id_cat]
        productos.append({
            "id_producto": pid,
            "nombre_producto": nombre,
            "id_categoria": id_cat,
            "precio_lista": round(base * random.uniform(0.85, 1.15), 2),
            "activo": "S" if random.random() > 0.08 else "N",
            "fecha_alta": (date(2015, 1, 1) + timedelta(days=random.randint(0, 2500))).isoformat(),
        })
        pid += 1

sucursales = [{"id_sucursal": i, "nombre_sucursal": n, "region": r,
               "provincia": p, "zona_comercial": z, "fecha_apertura": f}
              for i, n, r, p, z, f in SUCURSALES]

vendedores: list[dict] = []
for i in range(1, 41):
    vendedores.append({
        "id_vendedor": i,
        "nombre_vendedor": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
        "id_sucursal": random.randint(1, len(sucursales)),
        "fecha_ingreso": (date(2016, 1, 1) + timedelta(days=random.randint(0, 2900))).isoformat(),
        "turno": random.choice(TURNOS),
    })

clientes: list[dict] = []
for i in range(1, 301):
    ciudad, provincia = random.choice(CIUDADES)
    clientes.append({
        "id_cliente": i,
        "razon_social": f"{random.choice(PREFIJOS_CLIENTE)} {random.choice(NOMBRES_COMERCIALES)}",
        "tipo_cliente": random.choices(TIPOS_CLIENTE, weights=[55, 20, 15, 10])[0],
        "ciudad": ciudad,
        "provincia": provincia,
        "fecha_alta": (date(2015, 1, 1) + timedelta(days=random.randint(0, 3300))).isoformat(),
    })

medios_pago = [{"id_medio_pago": i, "descripcion": d} for i, d in MEDIOS_PAGO]

# --------------------------------------------------------------------------
# Paso 2: tabla de hechos (ventas) limpia
# --------------------------------------------------------------------------
IDS_PRODUCTO = [p["id_producto"] for p in productos]
IDS_SUCURSAL = [s["id_sucursal"] for s in sucursales]
IDS_VENDEDOR = [v["id_vendedor"] for v in vendedores]
IDS_CLIENTE = [c["id_cliente"] for c in clientes]
IDS_MEDIO = [m["id_medio_pago"] for m in medios_pago]
PRECIO_LISTA = {p["id_producto"]: p["precio_lista"] for p in productos}

ventas: list[dict] = []
id_venta = 0
id_pedido = 0
for _ in range(N_PEDIDOS):
    id_pedido += 1
    n_lineas = random.choice(LINEAS_POR_PEDIDO)
    fecha_pedido = FECHA_MIN + timedelta(days=random.randint(0, (FECHA_MAX - FECHA_MIN).days))
    id_suc = random.choice(IDS_SUCURSAL)
    id_vend = random.choice([v["id_vendedor"] for v in vendedores if v["id_sucursal"] == id_suc])
    id_cli = random.choice(IDS_CLIENTE)
    id_mp = random.choice(IDS_MEDIO)

    for _l in range(n_lineas):
        id_venta += 1
        id_prod = random.choice(IDS_PRODUCTO)
        # Inflacion a lo largo del periodo
        factor = 1.0 + 0.40 * ((fecha_pedido - FECHA_MIN).days / (FECHA_MAX - FECHA_MIN).days)
        precio = round(PRECIO_LISTA[id_prod] * factor * random.uniform(0.97, 1.05), 2)
        cantidad = random.choices([1, 2, 3, 4, 6, 8, 12, 18, 24, 36],
                                  weights=[28, 20, 16, 11, 8, 6, 5, 3, 2, 1])[0]
        descuento = random.choices([0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
                                   weights=[50, 13, 12, 10, 8, 5, 2])[0]
        ventas.append({
            "id_venta": id_venta,
            "id_pedido": f"PED-{id_pedido:06d}",
            "fecha_venta": fecha_pedido,
            "id_producto": id_prod,
            "id_sucursal": id_suc,
            "id_vendedor": id_vend,
            "id_cliente": id_cli,
            "id_medio_pago": id_mp,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "descuento": descuento,
        })

N_VENTAS = len(ventas)
print(f"[1] Dimensiones: {len(categorias)} categorias, {len(productos)} productos, "
      f"{len(sucursales)} sucursales, {len(vendedores)} vendedores, "
      f"{len(clientes)} clientes, {len(medios_pago)} medios de pago")
print(f"[1] Fact: {N_VENTAS} lineas de venta en {N_PEDIDOS} pedidos")

# --------------------------------------------------------------------------
# Paso 3: inyeccion de defectos
# --------------------------------------------------------------------------
base = list(range(N_VENTAS))
reporte: dict[str, int] = {}

# V1 - id_venta duplicado (viola la PK)
idx_v1 = random.sample(base, 180)
for i, j in zip(idx_v1, random.sample(base, 180)):
    ventas[i]["id_venta"] = ventas[j]["id_venta"]
reporte["V1"] = len(idx_v1)

# V2 - id_producto huerfano
idx_v2 = random.sample(base, 350)
for i in idx_v2:
    ventas[i]["id_producto"] = random.randint(9001, 9350)
reporte["V2"] = len(idx_v2)

# V3 - id_sucursal huerfano (mitad NULL, mitad ID inexistente)
idx_v3 = random.sample(base, 500)
for n, i in enumerate(idx_v3):
    if n % 2 == 0:
        ventas[i]["id_sucursal"] = None
    else:
        ventas[i]["id_sucursal"] = random.randint(901, 950)
reporte["V3"] = len(idx_v3)

# V4 - id_vendedor huerfano
idx_v4 = random.sample(base, 200)
for i in idx_v4:
    ventas[i]["id_vendedor"] = random.randint(501, 560)
reporte["V4"] = len(idx_v4)

# V5 - id_cliente huerfano
idx_v5 = random.sample(base, 280)
for i in idx_v5:
    ventas[i]["id_cliente"] = random.randint(8001, 8300)
reporte["V5"] = len(idx_v5)

# V12 - id_medio_pago huerfano
idx_v12 = random.sample(base, 150)
for i in idx_v12:
    ventas[i]["id_medio_pago"] = random.choice([9, 10, 99, 0])
reporte["V12"] = len(idx_v12)

# V6 - cantidad negativa (devolucion no marcada)
idx_v6 = random.sample(base, 900)
for i in idx_v6:
    ventas[i]["cantidad"] = -abs(ventas[i]["cantidad"])
reporte["V6"] = len(idx_v6)

# V7 - cantidad cero
idx_v7 = random.sample([x for x in base if x not in idx_v6], 260)
for i in idx_v7:
    ventas[i]["cantidad"] = 0
reporte["V7"] = len(idx_v7)

# V8 - fecha fuera del rango del negocio
idx_v8 = random.sample(base, 60)
for n, i in enumerate(idx_v8):
    ventas[i]["fecha_venta"] = (date(1900, 1, 1) if n % 3 == 0
                                else date(2030, 6, 15) if n % 3 == 1
                                else date(2025, 1, 1) + timedelta(days=random.randint(0, 900)))
reporte["V8"] = len(idx_v8)

# V9 - precio_unitario invalido (cero o negativo)
idx_v9 = random.sample(base, 120)
for n, i in enumerate(idx_v9):
    ventas[i]["precio_unitario"] = 0.0 if n % 3 else -round(random.uniform(100, 3000), 2)
reporte["V9"] = len(idx_v9)

# V10 - descuento fuera de rango (sin ambiguedad interpretativa)
idx_v10 = random.sample(base, 400)
for i in idx_v10:
    ventas[i]["descuento"] = random.choice([15, 20, 25, 30, -0.05, -1.0])
reporte["V10"] = len(idx_v10)


def descuento_efectivo(d):
    """Interpretacion unica y razonable de un descuento mal cargado."""
    if d is None:
        return 0.0
    if d > 1:
        d = d / 100.0
    return min(max(d, 0.0), 1.0)


# Importe neto recalculado para TODAS las lineas (unico origen de verdad)
for v in ventas:
    v["importe_neto"] = round(
        v["cantidad"] * v["precio_unitario"] * (1 - descuento_efectivo(v["descuento"])), 2
    )

# V11 - importe_neto que no cuadra.
# Se excluyen las lineas con importe 0 (cantidad 0 o precio 0): corromper un 0
# sigue dando 0 y la inconsistencia seria indetectable, inflando el conteo
# inyectado sin que el archivo lo refleje.
pool_v11 = [x for x in base if ventas[x]["importe_neto"] != 0]
idx_v11 = random.sample(pool_v11, 1500)
for i in idx_v11:
    ventas[i]["importe_neto"] = round(
        ventas[i]["importe_neto"] * random.choice([0.88, 1.15, 0.75, 1.22]), 2
    )
reporte["V11"] = len(idx_v11)

# D1 - clientes con id_cliente duplicado (misma clave, distinta razon social)
idx_d1 = random.sample(range(len(clientes)), 12)
clon_cliente = []
for i in idx_d1:
    c = dict(clientes[i])
    c["razon_social"] = c["razon_social"] + " (SUCURSAL)"
    c["tipo_cliente"] = random.choice(TIPOS_CLIENTE)
    clon_cliente.append(c)
clientes = clientes + clon_cliente
reporte["D1"] = len(idx_d1)

# D2 - productos con id_categoria huerfano
idx_d2 = random.sample(range(len(productos)), 5)
for i in idx_d2:
    productos[i]["id_categoria"] = random.randint(901, 910)
reporte["D2"] = len(idx_d2)

# D3 - vendedores con id_sucursal huerfano
idx_d3 = random.sample(range(len(vendedores)), 3)
for i in idx_d3:
    vendedores[i]["id_sucursal"] = random.randint(901, 910)
reporte["D3"] = len(idx_d3)

print("\n[3] Defectos inyectados")
for cod in sorted(reporte):
    print(f"    {cod:<5} {reporte[cod]:>7}")

# --------------------------------------------------------------------------
# Paso 4: serializacion
# --------------------------------------------------------------------------
def txt(v) -> str:
    return "" if v is None else str(v)


TABLAS = {
    "categorias": (
        ["id_categoria", "nombre_categoria", "departamento"],
        [[txt(c[k]) for k in ["id_categoria", "nombre_categoria", "departamento"]]
         for c in categorias],
    ),
    "productos": (
        ["id_producto", "nombre_producto", "id_categoria", "precio_lista", "activo", "fecha_alta"],
        [[txt(p[k]) for k in ["id_producto", "nombre_producto", "id_categoria",
                              "precio_lista", "activo", "fecha_alta"]] for p in productos],
    ),
    "sucursales": (
        ["id_sucursal", "nombre_sucursal", "region", "provincia",
         "zona_comercial", "fecha_apertura"],
        [[txt(s[k]) for k in ["id_sucursal", "nombre_sucursal", "region", "provincia",
                              "zona_comercial", "fecha_apertura"]] for s in sucursales],
    ),
    "vendedores": (
        ["id_vendedor", "nombre_vendedor", "id_sucursal", "fecha_ingreso", "turno"],
        [[txt(v[k]) for k in ["id_vendedor", "nombre_vendedor", "id_sucursal",
                              "fecha_ingreso", "turno"]] for v in vendedores],
    ),
    "clientes": (
        ["id_cliente", "razon_social", "tipo_cliente", "ciudad", "provincia", "fecha_alta"],
        [[txt(c[k]) for k in ["id_cliente", "razon_social", "tipo_cliente",
                              "ciudad", "provincia", "fecha_alta"]] for c in clientes],
    ),
    "medios_pago": (
        ["id_medio_pago", "descripcion"],
        [[txt(m[k]) for k in ["id_medio_pago", "descripcion"]] for m in medios_pago],
    ),
    "ventas": (
        ["id_venta", "id_pedido", "fecha_venta", "id_producto", "id_sucursal",
         "id_vendedor", "id_cliente", "id_medio_pago", "cantidad",
         "precio_unitario", "descuento", "importe_neto"],
        [[txt(v["id_venta"]), v["id_pedido"], v["fecha_venta"].isoformat(),
          txt(v["id_producto"]), txt(v["id_sucursal"]), txt(v["id_vendedor"]),
          txt(v["id_cliente"]), txt(v["id_medio_pago"]), txt(v["cantidad"]),
          str(v["precio_unitario"]), str(v["descuento"]),
          f"{v['importe_neto']:.2f}"] for v in ventas],
    ),
}

for nombre, (cabecera, filas) in TABLAS.items():
    ruta = SALIDA / f"{nombre}.csv"
    # UTF-8 SIN BOM: el BOM romperia el COPY de PostgreSQL en la primera columna.
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cabecera)
        w.writerows(filas)
    print(f"[4] {ruta.name:<18} {len(filas):>7} filas")

# --------------------------------------------------------------------------
# Paso 5: verificacion independiente
# --------------------------------------------------------------------------
def escanear(t: dict) -> dict[str, int]:
    """Cuenta defectos sobre un dict de tablas ya serializadas (todas str)."""
    def idx(nombre):
        cab = t[nombre][0]
        return [{c: fila[i] for i, c in enumerate(cab)} for fila in t[nombre][1]]

    v = idx("ventas")
    prods = idx("productos")
    sucs = idx("sucursales")
    vend = idx("vendedores")
    clis = idx("clientes")
    mps = idx("medios_pago")

    pk_prod = {r["id_producto"] for r in prods}
    pk_suc = {r["id_sucursal"] for r in sucs}
    pk_vend = {r["id_vendedor"] for r in vend}
    pk_cli = {r["id_cliente"] for r in clis}
    pk_mp = {r["id_medio_pago"] for r in mps}
    pk_cat = {r["id_categoria"] for r in idx("categorias")}

    med = {k: 0 for k in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8",
                          "V9", "V10", "V11", "V12", "D1", "D2", "D3"]}

    conteo_id: dict[str, int] = {}
    for r in v:
        conteo_id[r["id_venta"]] = conteo_id.get(r["id_venta"], 0) + 1
    med["V1"] = sum(c - 1 for c in conteo_id.values() if c > 1)

    for r in v:
        if r["id_producto"] not in pk_prod:
            med["V2"] += 1
        if r["id_sucursal"] == "" or r["id_sucursal"] not in pk_suc:
            med["V3"] += 1
        if r["id_vendedor"] not in pk_vend:
            med["V4"] += 1
        if r["id_cliente"] not in pk_cli:
            med["V5"] += 1
        if r["id_medio_pago"] not in pk_mp:
            med["V12"] += 1

        cant = int(r["cantidad"])
        if cant < 0:
            med["V6"] += 1
        if cant == 0:
            med["V7"] += 1

        f = r["fecha_venta"]
        if not ("2023-01-01" <= f <= "2024-12-31"):
            med["V8"] += 1

        pu = float(r["precio_unitario"])
        if pu <= 0:
            med["V9"] += 1

        d = float(r["descuento"])
        if d < 0 or d > 1:
            med["V10"] += 1

        esperado = cant * pu * (1 - descuento_efectivo(d))
        if abs(esperado - float(r["importe_neto"])) > 1.0:
            med["V11"] += 1

    conteo_cli: dict[str, int] = {}
    for r in clis:
        conteo_cli[r["id_cliente"]] = conteo_cli.get(r["id_cliente"], 0) + 1
    med["D1"] = sum(c - 1 for c in conteo_cli.values() if c > 1)

    med["D2"] = sum(1 for r in prods if r["id_categoria"] not in pk_cat)
    med["D3"] = sum(1 for r in vend if r["id_sucursal"] not in pk_suc)

    return med


en_memoria = escanear(TABLAS)

en_archivo_tablas: dict = {}
for nombre, (cabecera, _filas) in TABLAS.items():
    with (SALIDA / f"{nombre}.csv").open("r", newline="", encoding="utf-8") as fh:
        lector = csv.reader(fh)
        cab = next(lector)
        cuerpo = [fila for fila in lector]
    assert cab == cabecera, f"{nombre}: la cabecera cambio al escribir"
    en_archivo_tablas[nombre] = (cab, cuerpo)

en_archivo = escanear(en_archivo_tablas)

NOMBRES = {
    "V1": "id_venta duplicado (viola la PK)",
    "V2": "id_producto huerfano",
    "V3": "id_sucursal huerfano o NULL",
    "V4": "id_vendedor huerfano",
    "V5": "id_cliente huerfano",
    "V6": "cantidad negativa (devolucion no marcada)",
    "V7": "cantidad cero",
    "V8": "fecha_venta fuera de 2023-2024",
    "V9": "precio_unitario <= 0",
    "V10": "descuento fuera del rango 0-1",
    "V11": "importe_neto no cuadra con cantidad*precio*(1-desc)",
    "V12": "id_medio_pago huerfano",
    "D1": "clientes con id_cliente duplicado",
    "D2": "productos con id_categoria huerfano",
    "D3": "vendedores con id_sucursal huerfano",
}

print("\n[5] VERIFICACION INDEPENDIENTE")
print(f"    {'Cod':<6}{'Inyectado':>10}{'Memoria':>9}{'Archivo':>9}   Defecto")
fallos: list[str] = []
for cod in NOMBRES:
    if en_memoria[cod] != en_archivo[cod]:
        fallos.append(f"{cod}:MEM!=ARCH")
        nota = "  <-- MEMORIA != ARCHIVO"
    elif cod in reporte and abs(en_archivo[cod] - reporte[cod]) > 1:
        fallos.append(f"{cod}:{en_archivo[cod]}vs{reporte[cod]}")
        nota = "  <-- inyectado != medido"
    else:
        nota = ""
    esp = reporte.get(cod)
    print(f"    {cod:<6}{(esp if esp is not None else '-'):>10}"
          f"{en_memoria[cod]:>9}{en_archivo[cod]:>9}   {NOMBRES[cod]}{nota}")

filas_esperadas = {
    "categorias": len(categorias), "productos": len(productos),
    "sucursales": len(sucursales), "vendedores": len(vendedores),
    "clientes": len(clientes), "medios_pago": len(medios_pago),
    "ventas": N_VENTAS,
}
for nombre, esperadas in filas_esperadas.items():
    reales = len(en_archivo_tablas[nombre][1])
    if reales != esperadas:
        fallos.append(f"{nombre}:{reales}!={esperadas}")

print("\n    Filas por tabla (archivo vs esperado)")
for nombre, esperadas in filas_esperadas.items():
    reales = len(en_archivo_tablas[nombre][1])
    ok = "OK" if reales == esperadas else "REVISAR"
    print(f"      {nombre:<14}{reales:>8} / {esperadas:<8} {ok}")

# --------------------------------------------------------------------------
# Paso 6: clave de respuestas
# --------------------------------------------------------------------------
TECNICAS = {
    "V1": "`GROUP BY id_venta HAVING COUNT(*) > 1`. Agregar la PK despues de limpiar",
    "V2": "`LEFT JOIN productos p ON ... WHERE p.id_producto IS NULL`",
    "V3": "`LEFT JOIN sucursales s ... WHERE s.id_sucursal IS NULL` (incluye los NULL)",
    "V4": "`LEFT JOIN vendedores v ... WHERE v.id_vendedor IS NULL`",
    "V5": "`LEFT JOIN clientes c ... WHERE c.id_cliente IS NULL`",
    "V6": "Decision de negocio: son devoluciones. `CASE WHEN cantidad < 0 THEN 'Devolucion' END`",
    "V7": "`WHERE cantidad = 0`: lineas sin efecto en el total, decidir si se conservan",
    "V8": "`WHERE fecha_venta NOT BETWEEN '2023-01-01' AND '2024-12-31'`",
    "V9": "`WHERE precio_unitario <= 0`: revisar si son bonificaciones o errores de carga",
    "V10": "`WHERE descuento < 0 OR descuento > 1` + interpretar 15 -> 0,15",
    "V11": "Recalcular `cantidad * precio_unitario * (1 - descuento)` y comparar con tolerancia",
    "V12": "`LEFT JOIN medios_pago m ... WHERE m.id_medio_pago IS NULL`",
    "D1": "`GROUP BY id_cliente HAVING COUNT(*) > 1` y decidir cual version es la valida",
    "D2": "`LEFT JOIN categorias` desde productos: un producto sin categoria rompe el reporte por rubro",
    "D3": "`LEFT JOIN sucursales` desde vendedores: un vendedor sin sucursal no aparece en el ranking por local",
}

# Consultas de diagnostico, en SQL portable. Se embeben en la clave y ademas
# son ejecutadas por scripts/verificar_p2_sqlite.py contra un motor SQL real.
_JOIN_HUERFANO = ("SELECT COUNT(*) FROM ventas v LEFT JOIN {tabla} t "
                  "ON v.{fk} = t.{pk} WHERE t.{pk} IS NULL")
QUERIES = {
    "V1": ("SELECT SUM(c - 1) AS filas_extra FROM "
           "(SELECT COUNT(*) AS c FROM ventas GROUP BY id_venta HAVING COUNT(*) > 1) t"),
    "V2": _JOIN_HUERFANO.format(tabla="productos", fk="id_producto", pk="id_producto"),
    "V3": _JOIN_HUERFANO.format(tabla="sucursales", fk="id_sucursal", pk="id_sucursal"),
    "V4": _JOIN_HUERFANO.format(tabla="vendedores", fk="id_vendedor", pk="id_vendedor"),
    "V5": _JOIN_HUERFANO.format(tabla="clientes", fk="id_cliente", pk="id_cliente"),
    "V6": "SELECT COUNT(*) FROM ventas WHERE cantidad < 0",
    "V7": "SELECT COUNT(*) FROM ventas WHERE cantidad = 0",
    "V8": ("SELECT COUNT(*) FROM ventas "
           "WHERE fecha_venta < '2023-01-01' OR fecha_venta > '2024-12-31'"),
    "V9": "SELECT COUNT(*) FROM ventas WHERE precio_unitario <= 0",
    "V10": "SELECT COUNT(*) FROM ventas WHERE descuento < 0 OR descuento > 1",
    "V11": ("SELECT COUNT(*) FROM ventas WHERE ABS(cantidad * precio_unitario * "
            "(1 - CASE WHEN descuento > 1 THEN descuento / 100.0 "
            "WHEN descuento < 0 THEN 0 ELSE descuento END) - importe_neto) > 1"),
    "V12": _JOIN_HUERFANO.format(tabla="medios_pago", fk="id_medio_pago",
                                 pk="id_medio_pago"),
    "D1": ("SELECT SUM(c - 1) AS filas_extra FROM "
           "(SELECT COUNT(*) AS c FROM clientes GROUP BY id_cliente HAVING COUNT(*) > 1) t"),
    "D2": ("SELECT COUNT(*) FROM productos p LEFT JOIN categorias c "
           "ON p.id_categoria = c.id_categoria WHERE c.id_categoria IS NULL"),
    "D3": ("SELECT COUNT(*) FROM vendedores v LEFT JOIN sucursales s "
           "ON v.id_sucursal = s.id_sucursal WHERE s.id_sucursal IS NULL"),
}

lineas = [
    "# CLAVE DE RESPUESTAS — PROYECTO 2 (SQL) — NO ABRIR ANTES DE TERMINAR",
    "",
    "> Spoiler total. Usalo solo para autoevaluarte.",
    "",
    "## Números de control",
    "",
    "| Tabla | Filas |",
    "|---|---|",
]
for nombre in ["categorias", "productos", "sucursales", "vendedores",
               "clientes", "medios_pago", "ventas"]:
    lineas.append(f"| `{nombre}` | {len(en_archivo_tablas[nombre][1])} |")

lineas += [
    "",
    f"- `ventas` tiene **{N_PEDIDOS} pedidos** distintos con un promedio de "
    f"{N_VENTAS / N_PEDIDOS:.2f} líneas por pedido. El **ticket promedio** se calcula "
    "agrupando por `id_pedido`, no por `id_venta`.",
    "- Periodo válido del negocio: **2023-01-01 a 2024-12-31**.",
    f"- **{N_VENTAS - en_archivo['V11']}** de las {N_VENTAS} líneas tienen el importe bien calculado. "
    f"Las otras **{en_archivo['V11']}** no. Nunca confíes en una columna de importe sin recalcularla.",
    "",
    "---",
    "",
    "## Defectos inyectados y cómo se detectan",
    "",
    "| Cod | Defecto | Filas | Consulta / técnica |",
    "|---|---|---|---|",
]
for cod in NOMBRES:
    lineas.append(f"| {cod} | {NOMBRES[cod]} | {en_archivo[cod]} | {TECNICAS[cod]} |")

lineas += [
    "",
    "---",
    "",
    "## Consultas de verificación (spoiler: intentá escribirlas vos primero)",
    "",
    "Todas devuelven un único número. Si tu conteo coincide, tu diagnóstico está bien.",
    "Están escritas en SQL portable (sin `GREATEST`, sin casts propietarios) para que funcionen igual en PostgreSQL y en cualquier otro motor.",
    "",
    "```sql",
]
for cod in NOMBRES:
    lineas.append(f"-- @codigo {cod}  ({NOMBRES[cod]})")
    lineas.append(f"{QUERIES[cod]};")
    lineas.append("")
lineas += [
    "```",
    "",
    "### Nota sobre la interpretación del descuento",
    "",
    "En `V11` el descuento se interpreta así, y es la ÚNICA lectura razonable de los datos:",
    "",
    "```sql",
    "CASE WHEN descuento > 1 THEN descuento / 100.0   -- 15 significa 15%",
    "     WHEN descuento < 0 THEN 0                   -- un descuento negativo no existe",
    "     ELSE descuento END",
    "```",
    "",
    "Si tu recálculo usa otra interpretación, vas a contar de más en V11. Ese `CASE` es, "
    "en la práctica, una regla de negocio documentada: exactamente lo que un analista "
    "tiene que dejar escrito para que su número sea reproducible.",
    "",
    "---",
    "",
    "## Orden de trabajo obligatorio (y por qué)",
    "",
    "Si intentás crear las claves foráneas antes de limpiar, **PostgreSQL te va a rechazar la carga**. "
    "Ese error es el ejercicio, no un obstáculo:",
    "",
    "1. Crear las 7 tablas **sin** PK ni FK (`P2_01_crear_tablas.sql`).",
    "2. Cargar los CSV (el orden no importa sin FK).",
    "3. Ejecutar las consultas de diagnóstico de arriba y **documentar los conteos que encontrás**.",
    "4. Limpiar con `UPDATE` / `DELETE` / crear tablas nuevas con los datos corregidos.",
    "5. Recién ahora agregar PK y FK (`P2_02_agregar_constraints.sql`). Si falla, todavía hay basura.",
    "6. Construir las vistas de negocio y recién entonces responder las 10 preguntas.",
    "",
    "---",
    "",
    "## Preguntas de negocio (sin respuesta única: son las que se evalúan en entrevista)",
    "",
    f"1. Los **{en_archivo['V2']}** productos huérfanos: ¿son productos discontinuados que se "
    "siguen vendiendo con un código viejo, o errores de carga? ¿Cómo lo distinguirías?",
    f"2. Las **{en_archivo['V6']}** cantidades negativas: ¿devoluciones? Si lo son, "
    "¿el `importe_neto` negativo ya las refleja o las estás contando dos veces?",
    f"3. Los **{en_archivo['V3']}** casos con `id_sucursal` nulo: al hacer el ranking de sucursales, "
    "¿los excluís o creás una fila 'Sin asignar'? ¿Qué pasa con el total general en cada caso?",
    f"4. Los **{en_archivo['D1']}** clientes con clave duplicada: ¿son el mismo cliente cargado dos veces "
    "o dos sucursales del mismo cliente? Cada respuesta cambia el cálculo de LTV.",
    f"5. Las **{en_archivo['V11']}** líneas con importe inconsistente: ¿cuál es la fuente de verdad, "
    "el sistema o tu recálculo? ¿Cómo lo justificás ante un gerente?",
    "",
    "---",
    "",
    "## Estructura de archivos",
    "",
    "| Archivo | Qué es |",
    "|---|---|",
    "| `datos/p2/*.csv` | Las 7 tablas en crudo (UTF-8 sin BOM, listo para `COPY`) |",
    "| `scripts/P2_01_crear_tablas.sql` | DDL sin constraints |",
    "| `scripts/P2_02_agregar_constraints.sql` | PK y FK, para ejecutar al final |",
    "| `datos/p2/P2_CLAVE_NO_ABRIR.md` | Este archivo |",
    "",
]
RUTA_CLAVE = SALIDA / "P2_CLAVE_NO_ABRIR.md"
RUTA_CLAVE.write_text("\n".join(lineas), encoding="utf-8")
print(f"\n[6] Clave de respuestas escrita: {RUTA_CLAVE}")

if fallos:
    print(f"\n[!] ATENCION: {fallos}", file=sys.stderr)
    sys.exit(1)
print("\n[OK] Memoria == archivo en los 15 defectos y las 7 tablas tienen el tamano esperado.")
