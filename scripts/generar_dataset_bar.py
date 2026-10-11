"""
Genera el dataset del Proyecto 4: control de inventario de un bar.

LA IDEA CENTRAL
---------------
Este dataset no se genera "hacia adelante" (inventar ventas y que pase lo que pase).
Se genera HACIA ATRAS desde causas de merma conocidas:

  1. Se inventan las ventas del POS.
  2. Se calcula el uso TEORICO (ventas x recetas).
  3. Se construye el uso REAL aplicando 5 causas de merma con firma conocida.
  4. Se DERIVAN los conteos fisicos a partir del uso real y las compras.
  5. Se corrompe selectivamente lo REGISTRADO (comps sin anotar, remito sin cargar).

Por que importa: al derivar los conteos del uso real, el reporte de variacion
recupera EXACTAMENTE lo inyectado. Si no lo recuperara, el dataset seria basura
y el ejercicio no tendria solucion.

Las 5 causas y su firma (esto es lo que hay que aprender a distinguir):

  C1 OVER-POURING   +6% sobre todo el uso teorico de los insumos de cocteleria.
                    Firma: variacion positiva ANCHA, pareja, todos los periodos.
  C2 ROBO           350 ml/semana en 3 SKU premium.
                    Firma: variacion CONCENTRADA en pocos SKU de alto valor, sostenida.
  C3 ERROR DE CONTEO ron blanco, semana 12: subconteo de 2,5 envases.
                    Firma: pico POSITIVO en una semana y NEGATIVO en la siguiente
                    (el error se compensa). Par +/-, una sola vez.
  C4 COMP NO REGISTRADO  40 Mojitos en la semana 18 nunca entraron al POS.
                    Firma: pico POSITIVO de una semana, SIN compensacion despues.
  C5 PROBLEMA DE PAPEL   6 envases de gin entregados y nunca cargados (semana 8).
                    Firma: uso NEGATIVO (ventas > uso), un SKU, una semana.

La diferencia entre C3 y C4 es la clave del analisis profesional: las dos son
"un pico en una semana", pero solo el error de conteo se compensa despues.

Ejecutar:  <python> scripts/generar_dataset_bar.py
Salida:    datos/bar/*.csv + datos/bar/analisis_bar.db + datos/bar/BAR_CLAVE_NO_ABRIR.md
"""

from __future__ import annotations

import csv
import math
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

random.seed(20240615)

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "datos" / "bar"
SALIDA.mkdir(parents=True, exist_ok=True)

FECHA_INICIO = date(2024, 1, 1)      # lunes
N_SEMANAS = 26
N_DIAS = N_SEMANAS * 7               # 182
TURNOS = ["Tarde", "Noche"]

# --------------------------------------------------------------------------
# Insumos: (nombre, categoria, unidad_base, contenido_por_envase, costo_unitario)
# unidad_base 'ml'   -> se cuenta en envases (botin, barril, jarabe)
# unidad_base 'unidad' -> se cuenta por unidad (botella de cerveza, limon, vaso)
# --------------------------------------------------------------------------
INSUMOS = [
    # --- Destilados (botella de 700 ml) ---
    ("Vodka estandar", "Destilados", "ml", 700, 9800),
    ("Vodka premium", "Destilados", "ml", 700, 21500),
    ("Gin London Dry", "Destilados", "ml", 700, 16400),
    ("Gin premium", "Destilados", "ml", 700, 28900),
    ("Ron blanco", "Destilados", "ml", 700, 11200),
    ("Ron anejo", "Destilados", "ml", 700, 18700),
    ("Whisky estandar", "Destilados", "ml", 700, 14300),
    ("Whisky premium 12 anios", "Destilados", "ml", 700, 42600),
    ("Bourbon", "Destilados", "ml", 700, 23800),
    ("Tequila blanco", "Destilados", "ml", 700, 15900),
    ("Tequila reposado", "Destilados", "ml", 700, 27400),
    ("Mezcal artesanal", "Destilados", "ml", 700, 33500),
    ("Cognac", "Destilados", "ml", 700, 38700),
    ("Vermouth rojo", "Destilados", "ml", 700, 8900),
    ("Vermouth blanco", "Destilados", "ml", 700, 9200),
    ("Campari", "Destilados", "ml", 700, 15200),
    ("Aperol", "Destilados", "ml", 700, 14800),
    ("Amaretto", "Destilados", "ml", 700, 12600),
    ("Triple sec", "Destilados", "ml", 700, 10400),
    ("Licor de cafe", "Destilados", "ml", 700, 11900),
    ("Licor de durazno", "Destilados", "ml", 700, 10800),
    ("Fernet", "Destilados", "ml", 750, 13100),
    ("Bitter italiano", "Destilados", "ml", 700, 9900),
    ("Sake", "Destilados", "ml", 720, 17600),
    ("Pisco", "Destilados", "ml", 700, 16800),
    ("Cachaca", "Destilados", "ml", 700, 10700),
    # --- Vinos (botella de 750 ml) ---
    ("Malbec", "Vinos", "ml", 750, 7600),
    ("Cabernet Sauvignon", "Vinos", "ml", 750, 8100),
    ("Chardonnay", "Vinos", "ml", 750, 7200),
    ("Sauvignon Blanc", "Vinos", "ml", 750, 7800),
    ("Espumante brut", "Vinos", "ml", 750, 9400),
    ("Rosado", "Vinos", "ml", 750, 6900),
    # --- Cervezas (por unidad) ---
    ("Cerveza IPA botella", "Cervezas", "unidad", 1, 1450),
    ("Cerveza Lager botella", "Cervezas", "unidad", 1, 1100),
    ("Cerveza Negra botella", "Cervezas", "unidad", 1, 1520),
    ("Cerveza Trigo botella", "Cervezas", "unidad", 1, 1390),
    ("Cerveza Sin Alcohol botella", "Cervezas", "unidad", 1, 1180),
    # --- Barril (30 litros por barril) ---
    ("Barril Lager 30L", "Barriles", "ml", 30000, 78000),
    ("Barril IPA 30L", "Barriles", "ml", 30000, 96000),
    # --- Mixers (botella de 1 litro) ---
    ("Agua tonica", "Mixers", "ml", 1000, 2100),
    ("Ginger ale", "Mixers", "ml", 1000, 2300),
    ("Jugo de limon", "Mixers", "ml", 1000, 1950),
    ("Jugo de naranja", "Mixers", "ml", 1000, 2400),
    ("Jugo de arandano", "Mixers", "ml", 1000, 3100),
    ("Agua con gas", "Mixers", "ml", 1000, 1500),
    ("Soda", "Mixers", "ml", 1000, 1300),
    ("Gaseosa cola", "Mixers", "ml", 1000, 2200),
    # --- Jarabes (botella de 750 ml) ---
    ("Jarabe simple", "Jarabes", "ml", 750, 2600),
    ("Jarabe de goma", "Jarabes", "ml", 750, 2900),
    ("Granadina", "Jarabes", "ml", 750, 3200),
    ("Sirope de agave", "Jarabes", "ml", 750, 4100),
    ("Jarabe de coco", "Jarabes", "ml", 750, 3600),
    # --- Amargos (frasco de 200 ml) ---
    ("Angostura", "Amargos", "ml", 200, 8900),
    ("Bitter de naranja", "Amargos", "ml", 200, 7600),
    ("Bitter de chocolate", "Amargos", "ml", 200, 8200),
    # --- Frescos (por unidad) ---
    ("Limon", "Frescos", "unidad", 1, 320),
    ("Lima", "Frescos", "unidad", 1, 380),
    ("Naranja", "Frescos", "unidad", 1, 290),
    ("Menta fresca", "Frescos", "unidad", 1, 850),
    ("Albahaca fresca", "Frescos", "unidad", 1, 900),
    ("Jengibre", "Frescos", "unidad", 1, 1100),
    ("Huevo", "Frescos", "unidad", 1, 210),
    # --- Insumos secos (por unidad) ---
    ("Azucar", "Secos", "unidad", 1, 1300),
    ("Sal", "Secos", "unidad", 1, 700),
    ("Cafe en grano", "Secos", "unidad", 1, 9800),
    ("Canela", "Secos", "unidad", 1, 1900),
    # --- Hielo ---
    ("Bolsa de hielo 2kg", "Hielo", "unidad", 1, 2600),
    # --- Descartables ---
    ("Vaso highball", "Descartables", "unidad", 1, 180),
    ("Vaso old fashioned", "Descartables", "unidad", 1, 210),
    ("Servilleta", "Descartables", "unidad", 1, 45),
    ("Sorbete", "Descartables", "unidad", 1, 60),
    ("Agitador", "Descartables", "unidad", 1, 95),
    ("Vaso de shot", "Descartables", "unidad", 1, 110),
]

# --------------------------------------------------------------------------
# Carta y recetas. Los tragos directos tienen una receta de una linea.
# El precio de venta esta calibrado para un pour cost razonable.
# --------------------------------------------------------------------------
CARTA = [
    # (nombre, categoria, precio_venta, [(insumo, cantidad)])
    ("Negroni", "Cocteles", 7800, [("Gin London Dry", 30), ("Campari", 30), ("Vermouth rojo", 30)]),
    ("Gin Tonic", "Cocteles", 7200, [("Gin London Dry", 50), ("Agua tonica", 150), ("Limon", 0.25)]),
    ("Fernet con Cola", "Cocteles", 6400, [("Fernet", 60), ("Gaseosa cola", 180)]),
    ("Mojito", "Cocteles", 7100, [("Ron blanco", 50), ("Jarabe simple", 20), ("Lima", 0.5),
                                  ("Menta fresca", 0.2), ("Soda", 100)]),
    ("Daiquiri", "Cocteles", 7400, [("Ron blanco", 60), ("Jarabe simple", 25), ("Lima", 0.5)]),
    ("Margarita", "Cocteles", 7900, [("Tequila blanco", 50), ("Triple sec", 25), ("Lima", 0.5)]),
    ("Old Fashioned", "Cocteles", 9800, [("Bourbon", 60), ("Jarabe de goma", 10),
                                         ("Angostura", 1.5), ("Naranja", 0.2)]),
    ("Whisky Highball", "Cocteles", 8200, [("Whisky estandar", 50), ("Soda", 140), ("Limon", 0.2)]),
    ("Vodka Tonic", "Cocteles", 6900, [("Vodka estandar", 50), ("Agua tonica", 150), ("Lima", 0.25)]),
    ("Aperol Spritz", "Cocteles", 7600, [("Aperol", 60), ("Espumante brut", 90), ("Soda", 30)]),
    ("Caipirinha", "Cocteles", 7300, [("Cachaca", 60), ("Lima", 0.5), ("Azucar", 0.05)]),
    ("Cosmopolitan", "Cocteles", 7700, [("Vodka premium", 45), ("Triple sec", 20),
                                        ("Jugo de arandano", 40), ("Lima", 0.3)]),
    ("Paloma", "Cocteles", 7400, [("Tequila reposado", 50), ("Gaseosa cola", 30),
                                  ("Jugo de limon", 40), ("Sal", 0.02)]),
    ("Moscow Mule", "Cocteles", 7300, [("Vodka estandar", 50), ("Ginger ale", 150), ("Lima", 0.3)]),
    ("Whisky Sour", "Cocteles", 8400, [("Whisky estandar", 60), ("Jugo de limon", 30),
                                       ("Jarabe simple", 20), ("Huevo", 0.5)]),
    # --- Directos de barra ---
    ("Malbec copa", "Vinos", 5400, [("Malbec", 150)]),
    ("Chardonnay copa", "Vinos", 5100, [("Chardonnay", 150)]),
    ("Espumante copa", "Vinos", 5200, [("Espumante brut", 120)]),
    ("Cerveza IPA botella", "Cervezas", 4200, [("Cerveza IPA botella", 1)]),
    ("Cerveza Lager botella", "Cervezas", 3400, [("Cerveza Lager botella", 1)]),
    ("Pinta de barril Lager", "Barriles", 3800, [("Barril Lager 30L", 500)]),
    ("Tequila shot", "Destilados", 4500, [("Tequila blanco", 45)]),
    ("Whisky shot premium", "Destilados", 8900, [("Whisky premium 12 anios", 45)]),
    ("Gin premium tonic", "Cocteles", 9600, [("Gin premium", 50), ("Agua tonica", 150), ("Lima", 0.25)]),
]

# Popularidad relativa de cada trago (mas alto = mas vendido)
POPULARIDAD = {
    "Fernet con Cola": 130, "Gin Tonic": 125, "Cerveza Lager botella": 120,
    "Cerveza IPA botella": 105, "Pinta de barril Lager": 115, "Mojito": 100,
    "Malbec copa": 95, "Vodka Tonic": 90, "Negroni": 85, "Aperol Spritz": 80,
    "Margarita": 70, "Whisky Highball": 65, "Moscow Mule": 60, "Daiquiri": 55,
    "Caipirinha": 50, "Whisky shot premium": 48, "Paloma": 45, "Cosmopolitan": 42,
    "Chardonnay copa": 40, "Whisky Sour": 38, "Old Fashioned": 35,
    "Tequila shot": 34, "Espumante copa": 30, "Gin premium tonic": 28,
}

# Multiplicador por dia de la semana (0=lunes ... 6=domingo)
MULT_DIA = {0: 0.55, 1: 0.60, 2: 0.70, 3: 0.95, 4: 1.65, 5: 1.85, 6: 0.85}
MULT_TURNO = {"Tarde": 0.4, "Noche": 1.0}

# --------------------------------------------------------------------------
# Las 5 causas de merma inyectadas (la "verdad" que el analisis debe recuperar)
# --------------------------------------------------------------------------
OVER_POUR = 1.06                                    # C1: +6% sobre el teorico
ROBO_POR_SEMANA = {                                 # C2: ml robados por semana
    "Whisky premium 12 anios": 350,
    "Tequila reposado": 350,
    "Mezcal artesanal": 350,
}
CONTEO_ERRONEO = ("Ron blanco", 12, 2.5)            # C3: (insumo, semana, envases de menos)
COMP_NO_REGISTRADO = ("Mojito", 18, 40)             # C4: (trago, semana, unidades sin cobrar)
REMITO_NO_CARGADO = ("Gin London Dry", 8)           # C5: (insumo, semana) -> la entrega no se cargó
# Para que C5 exista tiene que haber una entrega en esa semana. Se fuerza el pedido.
ENTREGAS_FORZADAS = {("Gin London Dry", 8): 6}

NOMBRES_INSUMO = [i[0] for i in INSUMOS]
IDX_INSUMO = {n: k + 1 for k, n in enumerate(NOMBRES_INSUMO)}
CONTENIDO = {i[0]: (i[2], i[3], i[4]) for i in INSUMOS}   # nombre -> (unidad, contenido, costo)

print(f"[1] {len(INSUMOS)} insumos, {len(CARTA)} tragos en carta")

# --------------------------------------------------------------------------
# Paso 1: ventas del POS
# --------------------------------------------------------------------------
ventas: list[dict] = []
for d in range(N_DIAS):
    fecha = FECHA_INICIO + timedelta(days=d)
    dow = fecha.weekday()
    semana = d // 7 + 1
    for nombre_trago, _cat, precio, _receta in CARTA:
        base = POPULARIDAD[nombre_trago] * MULT_DIA[dow]
        for turno in TURNOS:
            lam = base * MULT_TURNO[turno] / 10.0
            cant = max(0, int(random.gauss(lam, lam * 0.35)))
            if cant == 0:
                continue
            ventas.append({
                "fecha": fecha, "semana": semana, "turno": turno,
                "id_trago": nombre_trago, "cantidad": cant,
                "precio_unitario": precio,
            })
print(f"[1] {len(ventas)} lineas de venta (POS, antes de aplicar el comp)")

# Se guarda una copia con TODAS las ventas: es la realidad fisica.
ventas_real = [dict(v) for v in ventas]

# ---- C4: el comp no registrado. 40 Mojitos de la semana 18 nunca entraron al POS.
trago_comp, semana_comp, cant_comp = COMP_NO_REGISTRADO
pendiente = cant_comp
for v in ventas:
    if pendiente <= 0:
        break
    if v["id_trago"] == trago_comp and v["semana"] == semana_comp:
        quitar = min(pendiente, v["cantidad"])
        v["cantidad"] -= quitar
        pendiente -= quitar
ventas = [v for v in ventas if v["cantidad"] > 0]
comp_aplicado = cant_comp - pendiente
print(f"[2] C4 comp no registrado: {comp_aplicado} '{trago_comp}' quitados del POS (semana {semana_comp})")

# --------------------------------------------------------------------------
# Paso 2: uso TEORICO (desde el POS registrado) y uso REAL (desde la realidad)
# --------------------------------------------------------------------------
RECETA_POR_TRAGO = {n: r for n, _c, _p, r in
                    [(n, c, p, r) for n, c, p, r in CARTA]}

def uso_desde(fuente: list[dict]) -> dict[tuple[str, int], float]:
    """{(insumo, semana): cantidad} a partir de las ventas indicadas."""
    acc: dict[tuple[str, int], float] = {}
    for v in fuente:
        for insumo, cant in RECETA_POR_TRAGO[v["id_trago"]]:
            clave = (insumo, v["semana"])
            acc[clave] = acc.get(clave, 0.0) + cant * v["cantidad"]
    return acc

uso_teorico = uso_desde(ventas)          # desde el POS REGISTRADO (con el comp faltante)
uso_real = uso_desde(ventas_real)        # desde la REALIDAD fisica

# ---- C1: over-pouring, +6% sobre todo el uso teorico de insumos de cocteleria
insumos_coctel = set()
for nombre_trago, cat, _p, receta in CARTA:
    if cat == "Cocteles":
        for insumo, _c in receta:
            insumos_coctel.add(insumo)

for clave in list(uso_real):
    insumo, _sem = clave
    if insumo in insumos_coctel:
        uso_real[clave] *= OVER_POUR

# ---- C2: robo sostenido en 3 SKU premium
for insumo, ml_por_semana in ROBO_POR_SEMANA.items():
    for sem in range(1, N_SEMANAS + 1):
        clave = (insumo, sem)
        uso_real[clave] = uso_real.get(clave, 0.0) + ml_por_semana

print(f"[2] C1 over-pouring: +{(OVER_POUR - 1) * 100:.0f}% sobre {len(insumos_coctel)} insumos de cocteleria")
print(f"[2] C2 robo: {len(ROBO_POR_SEMANA)} SKU x {list(ROBO_POR_SEMANA.values())[0]} ml/semana")

# --------------------------------------------------------------------------
# Paso 3: trayectoria de stock y compras (a nivel de REALIDAD, sin errores)
# --------------------------------------------------------------------------
# Par level: ~3 semanas de consumo promedio, con un minimo.
consumo_prom: dict[str, float] = {}
for insumo in NOMBRES_INSUMO:
    total = sum(v for (i, _s), v in uso_real.items() if i == insumo)
    consumo_prom[insumo] = total / N_SEMANAS if total else 0.0

par_envases: dict[str, float] = {}
for insumo in NOMBRES_INSUMO:
    unidad, contenido, _costo = CONTENIDO[insumo]
    cons = consumo_prom[insumo] / contenido if contenido else 0.0
    par_envases[insumo] = max(2.0, cons * 3.0)

# Conteo inicial: un poco por encima del par
conteo_real: dict[str, float] = {
    i: round(par_envases[i] * random.uniform(1.0, 1.3), 2) for i in NOMBRES_INSUMO
}
registro_conteos_real: list[dict] = [{
    "fecha": FECHA_INICIO - timedelta(days=1), "semana": 0,
    "id_insumo": i, "cantidad": conteo_real[i],
} for i in NOMBRES_INSUMO]

compras: list[dict] = []
trayectoria: dict[str, float] = dict(conteo_real)

for sem in range(1, N_SEMANAS + 1):
    fecha_fin = FECHA_INICIO + timedelta(days=sem * 7 - 1)
    for insumo in NOMBRES_INSUMO:
        unidad, contenido, costo = CONTENIDO[insumo]
        uso_ml = uso_real.get((insumo, sem), 0.0)
        uso_env = uso_ml / contenido
        objetivo = par_envases[insumo] * random.uniform(0.9, 1.15)
        faltante = uso_env + objetivo - trayectoria[insumo]
        envases = max(0, math.ceil(faltante)) if faltante > 0 else 0
        # Entregas forzadas: garantizan que exista un remito en la semana que C5
        # va a dejar sin cargar. Si no, la causa no existiria en los datos.
        envases = max(envases, ENTREGAS_FORZADAS.get((insumo, sem), 0))
        if envases > 0:
            # Deriva de precios de compra: el costo sube con el tiempo (inflacion)
            factor = 1.0 + 0.09 * (sem / N_SEMANAS)
            compras.append({
                "fecha": fecha_fin - timedelta(days=random.randint(0, 5)),
                "semana": sem, "id_insumo": insumo, "cantidad": envases,
                "precio_unitario": round(costo * factor, 2),
            })
        trayectoria[insumo] = trayectoria[insumo] + envases - uso_env
        registro_conteos_real.append({
            "fecha": fecha_fin, "semana": sem,
            "id_insumo": insumo, "cantidad": round(trayectoria[insumo], 2),
        })

print(f"[3] {len(compras)} compras, {len(registro_conteos_real)} registros de conteo")

# --------------------------------------------------------------------------
# Paso 4: corromper lo REGISTRADO (C3 y C5) sin tocar la realidad fisica
# --------------------------------------------------------------------------
conteos = registro_conteos_real

# ---- C3: error de conteo. El conteo REGISTRADO de la semana 12 queda bajo.
insumo_c3, sem_c3, env_c3 = CONTEO_ERRONEO
corregidos = 0
for c in conteos:
    if c["id_insumo"] == insumo_c3 and c["semana"] == sem_c3:
        c["cantidad"] = round(c["cantidad"] - env_c3, 2)
        corregidos += 1
print(f"[4] C3 error de conteo: '{insumo_c3}' semana {sem_c3} con {env_c3} envases de menos "
      f"({corregidos} registro)")

# ---- C5: remito no cargado. La entrega llego pero no esta en el sistema.
# La magnitud de la causa es la entrega REAL de esa semana, no un numero elegido
# a mano: la causa es "el remito no se cargo", no "se perdieron N envases".
insumo_c5, sem_c5 = REMITO_NO_CARGADO
env_c5 = 0
for c in compras:
    if c["id_insumo"] == insumo_c5 and c["semana"] == sem_c5:
        env_c5 += c["cantidad"]
        c["cantidad"] = 0
compras = [c for c in compras if c["cantidad"] > 0]
print(f"[4] C5 remito no cargado: '{insumo_c5}' semana {sem_c5}, "
      f"{env_c5} envases entregados y no registrados")
if env_c5 == 0:
    print("[!] C5 no se pudo inyectar: no hubo entrega en esa semana", file=sys.stderr)
    sys.exit(1)

# --------------------------------------------------------------------------
# Paso 5: tablas derivadas y serializacion
# --------------------------------------------------------------------------
insumos_tab = [{
    "id_insumo": IDX_INSUMO[n], "nombre_insumo": n, "categoria": cat,
    "unidad_base": uni, "contenido_por_envase": cont, "costo_actual": costo,
} for n, cat, uni, cont, costo in INSUMOS]

carta_tab = [{"id_trago": n, "nombre_trago": n, "categoria": cat, "precio_venta": p}
             for n, cat, p, _r in CARTA]

recetas_tab = []
for n, _cat, _p, receta in CARTA:
    for insumo, cant in receta:
        recetas_tab.append({"id_trago": n, "id_insumo": IDX_INSUMO[insumo], "cantidad": cant})

ventas_tab = [{
    "fecha": v["fecha"].isoformat(), "semana": v["semana"], "turno": v["turno"],
    "id_trago": v["id_trago"], "cantidad": v["cantidad"],
    "precio_unitario": f"{v['precio_unitario']:.2f}",
    "importe": f"{v['cantidad'] * v['precio_unitario']:.2f}",
} for v in ventas]

compras_tab = [{
    "fecha": c["fecha"].isoformat(), "semana": c["semana"],
    "id_insumo": IDX_INSUMO[c["id_insumo"]], "cantidad": c["cantidad"],
    "precio_unitario": f"{c['precio_unitario']:.2f}",
    "importe": f"{c['cantidad'] * c['precio_unitario']:.2f}",
} for c in compras]

conteos_tab = [{
    "fecha": c["fecha"].isoformat(), "semana": c["semana"],
    "id_insumo": IDX_INSUMO[c["id_insumo"]], "cantidad": c["cantidad"],
} for c in conteos]

calendario_tab = []
DIAS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
for d in range(N_DIAS):
    f = FECHA_INICIO + timedelta(days=d)
    calendario_tab.append({
        "fecha": f.isoformat(), "semana": d // 7 + 1,
        # Dia en espanol: strftime('%A') depende del locale del sistema y devuelve
        # el nombre en ingles, lo cual rompe la coherencia de un dataset en espanol.
        "dia_semana": DIAS_ES[f.weekday()], "mes": f.strftime("%Y-%m"),
    })

TABLAS = {
    "insumos": (["id_insumo", "nombre_insumo", "categoria", "unidad_base",
                 "contenido_por_envase", "costo_actual"], insumos_tab),
    "carta": (["id_trago", "nombre_trago", "categoria", "precio_venta"], carta_tab),
    "recetas": (["id_trago", "id_insumo", "cantidad"], recetas_tab),
    "calendario": (["fecha", "semana", "dia_semana", "mes"], calendario_tab),
    "ventas": (["fecha", "semana", "turno", "id_trago", "cantidad",
                "precio_unitario", "importe"], ventas_tab),
    "compras": (["fecha", "semana", "id_insumo", "cantidad",
                 "precio_unitario", "importe"], compras_tab),
    "conteos": (["fecha", "semana", "id_insumo", "cantidad"], conteos_tab),
}

for nombre, (cab, filas) in TABLAS.items():
    with (SALIDA / f"{nombre}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cab)
        for f in filas:
            w.writerow([f[c] for c in cab])
    print(f"[5] {nombre + '.csv':<20}{len(filas):>7} filas")

# --------------------------------------------------------------------------
# Paso 6: VERIFICACION — el reporte de variacion recupera las causas inyectadas?
# --------------------------------------------------------------------------
TIPOS = {
    "insumos": {"id_insumo": "INTEGER", "nombre_insumo": "TEXT", "categoria": "TEXT",
                "unidad_base": "TEXT", "contenido_por_envase": "REAL",
                "costo_actual": "REAL"},
    "carta": {"id_trago": "TEXT", "nombre_trago": "TEXT", "categoria": "TEXT",
              "precio_venta": "REAL"},
    "recetas": {"id_trago": "TEXT", "id_insumo": "INTEGER", "cantidad": "REAL"},
    "calendario": {"fecha": "TEXT", "semana": "INTEGER", "dia_semana": "TEXT", "mes": "TEXT"},
    "ventas": {"fecha": "TEXT", "semana": "INTEGER", "turno": "TEXT", "id_trago": "TEXT",
               "cantidad": "INTEGER", "precio_unitario": "REAL", "importe": "REAL"},
    "compras": {"fecha": "TEXT", "semana": "INTEGER", "id_insumo": "INTEGER",
                "cantidad": "INTEGER", "precio_unitario": "REAL", "importe": "REAL"},
    "conteos": {"fecha": "TEXT", "semana": "INTEGER", "id_insumo": "INTEGER",
                "cantidad": "REAL"},
}

DB = SALIDA / "analisis_bar.db"
DB.unlink(missing_ok=True)
con = sqlite3.connect(DB)
for nombre, cols in TIPOS.items():
    defs = ", ".join(f"{c} {t}" for c, t in cols.items())
    con.execute(f"CREATE TABLE {nombre} ({defs})")
    cab, filas = TABLAS[nombre]
    con.executemany(
        f"INSERT INTO {nombre} ({', '.join(cab)}) VALUES ({', '.join('?' * len(cab))})",
        [[f[c] for c in cab] for f in filas],
    )
con.commit()

# --- El reporte de variacion, calculado por SQL (no por Python) ---
# OJO con el orden de evaluacion: WHERE se aplica ANTES que las funciones de
# ventana. Si se filtra semana > 0 en la misma consulta que calcula LAG(), la
# fila de la semana 0 desaparece antes del calculo y la primera semana de cada
# insumo queda con LAG = NULL. Por eso el filtro va en una CTE exterior.
VARIACION_SQL = """
WITH base AS (
    SELECT c.id_insumo, c.semana,
           ((LAG(c.cantidad) OVER (PARTITION BY c.id_insumo ORDER BY c.semana))
             + COALESCE(p.entregas, 0) - c.cantidad) * i.contenido_por_envase AS ml
    FROM conteos c
    JOIN insumos i ON i.id_insumo = c.id_insumo
    LEFT JOIN (SELECT id_insumo, semana, SUM(cantidad) AS entregas
               FROM compras GROUP BY id_insumo, semana) p
           ON p.id_insumo = c.id_insumo AND p.semana = c.semana
),
uso_real AS (SELECT * FROM base WHERE semana > 0),
uso_teorico AS (
    SELECT r.id_insumo, v.semana, SUM(r.cantidad * v.cantidad) AS ml
    FROM ventas v JOIN recetas r ON r.id_trago = v.id_trago
    GROUP BY r.id_insumo, v.semana
)
SELECT ur.id_insumo, i.nombre_insumo, i.categoria, ur.semana,
       ROUND(ur.ml, 2) AS uso_real_ml,
       ROUND(COALESCE(ut.ml, 0), 2) AS uso_teorico_ml,
       ROUND(ur.ml - COALESCE(ut.ml, 0), 2) AS variacion_ml,
       ROUND((ur.ml - COALESCE(ut.ml, 0))
             * (i.costo_actual / i.contenido_por_envase), 2) AS variacion_pesos
FROM uso_real ur
JOIN insumos i ON i.id_insumo = ur.id_insumo
LEFT JOIN uso_teorico ut ON ut.id_insumo = ur.id_insumo AND ut.semana = ur.semana
"""

filas_var = con.execute(VARIACION_SQL).fetchall()
print(f"\n[6] Reporte de variacion calculado por SQL: {len(filas_var)} filas (insumo x semana)")

var = {}
pesos = {}
uso_real_ml = {}
uso_teorico_ml = {}
for row in filas_var:
    _id, nombre, _cat, sem, ur, ut, v, p = row
    var[(nombre, sem)] = v
    pesos[(nombre, sem)] = p
    uso_real_ml[(nombre, sem)] = ur
    uso_teorico_ml[(nombre, sem)] = ut

fallos: list[str] = []

# --- C2: robo. La firma correcta NO es el volumen, es la PLATA. ---
# Los mixers tienen volumen enorme: su 6% de over-pouring genera mas mililitros
# absolutos que 350 ml robados de un whisky premium. Ordenar por ml esconde el
# robo. Un gerente de bar piensa en pesos, no en mililitros.
acum_ml: dict[str, float] = {}
acum_pesos: dict[str, float] = {}
for (nombre, _sem), p in pesos.items():
    acum_pesos[nombre] = acum_pesos.get(nombre, 0.0) + p
for (nombre, _sem), v in var.items():
    acum_ml[nombre] = acum_ml.get(nombre, 0.0) + v

top_ml = sorted(acum_ml.items(), key=lambda kv: -kv[1])[:5]
top_pesos = sorted(acum_pesos.items(), key=lambda kv: -kv[1])[:5]

print("\n    Top 5 por VARIACION EN MILILITROS (metrica enganosa):")
for n, v in top_ml:
    print(f"      {n:<28}{v:>12,.0f} ml")
print("\n    Top 5 por VARIACION EN PESOS (metrica correcta):")
for n, v in top_pesos:
    print(f"      {n:<28}{v:>14,.0f} $")

robados = set(ROBO_POR_SEMANA)
if not robados.issubset({n for n, _v in top_pesos[:3]}):
    fallos.append(f"C2 no detectable por pesos: top3={[n for n, _v in top_pesos[:3]]} "
                  f"vs robados={sorted(robados)}")

# --- C3: error de conteo. Par + / - en semanas consecutivas, misma magnitud ---
v_c3_pos = var.get((insumo_c3, sem_c3), 0.0)
v_c3_neg = var.get((insumo_c3, sem_c3 + 1), 0.0)
esperado_c3 = env_c3 * CONTENIDO[insumo_c3][1]
print(f"\n    C3 error de conteo en '{insumo_c3}':")
print(f"      semana {sem_c3}: {v_c3_pos:>+12,.0f} ml   (esperado ~{esperado_c3:+,.0f})")
print(f"      semana {sem_c3 + 1}: {v_c3_neg:>+12,.0f} ml   (debe ser negativo)")
if not (v_c3_pos > 0 and v_c3_neg < 0):
    fallos.append(f"C3 sin par +/-: {v_c3_pos:.0f} / {v_c3_neg:.0f}")

# --- C4: comp no registrado. Pico positivo SIN compensacion al mes siguiente ---
trago_c4, sem_c4, cant_c4 = COMP_NO_REGISTRADO
v_c4_sem = var.get(("Ron blanco", sem_c4), 0.0)
v_c4_prev = var.get(("Ron blanco", sem_c4 - 1), 0.0)
v_c4_next = var.get(("Ron blanco", sem_c4 + 1), 0.0)
print(f"\n    C4 comp no registrado ({comp_aplicado} '{trago_c4}' en semana {sem_c4}):")
print(f"      semana {sem_c4 - 1}: {v_c4_prev:>+12,.0f} ml")
print(f"      semana {sem_c4}:     {v_c4_sem:>+12,.0f} ml   (pico)")
print(f"      semana {sem_c4 + 1}: {v_c4_next:>+12,.0f} ml   (vuelve a la normalidad, sin compensar)")
if not (v_c4_sem > v_c4_prev and v_c4_sem > v_c4_next):
    fallos.append(f"C4 no es un pico aislado: {v_c4_prev:.0f} / {v_c4_sem:.0f} / {v_c4_next:.0f}")

# --- C5: remito no cargado. Uso NEGATIVO (variacion negativa) en un SKU y semana ---
v_c5 = var.get((insumo_c5, sem_c5), 0.0)
esperado_c5 = -env_c5 * CONTENIDO[insumo_c5][1]
v_c5_prev = var.get((insumo_c5, sem_c5 - 1), 0.0)
v_c5_next = var.get((insumo_c5, sem_c5 + 1), 0.0)
print(f"\n    C5 remito no cargado en '{insumo_c5}' semana {sem_c5}:")
print(f"      semana {sem_c5 - 1}: {v_c5_prev:>+12,.0f} ml")
print(f"      semana {sem_c5}:     {v_c5:>+12,.0f} ml   (esperado ~{esperado_c5:+,.0f})")
print(f"      semana {sem_c5 + 1}: {v_c5_next:>+12,.0f} ml")
if not (v_c5 < v_c5_prev and v_c5 < v_c5_next):
    fallos.append(f"C5 no es un minimo local: {v_c5_prev:.0f} / {v_c5:.0f} / {v_c5_next:.0f}")

# --- C1: over-pouring. Mediana de la variacion % sobre el teorico, en cocteleria ---
# Se compara contra el teorico (no contra ml absolutos) porque el over-pouring es
# un porcentaje constante sobre TODO el consumo de cocteleria.
pcts = sorted(
    100.0 * var[(n, s)] / uso_teorico_ml[(n, s)]
    for (n, s) in var
    if n in insumos_coctel and uso_teorico_ml.get((n, s)) not in (None, 0)
)
mediana = pcts[len(pcts) // 2] if pcts else 0.0
print(f"\n    C1 over-pouring: mediana de variacion % sobre el teorico en cocteleria = "
      f"{mediana:.1f}% (esperado ~{(OVER_POUR - 1) * 100:.1f}%)")
if abs(mediana - (OVER_POUR - 1) * 100) > 3:
    fallos.append(f"C1 fuera de rango: {mediana:.1f}%")

# --- Costo total de la merma: el numero que le importa al dueno ---
total_pesos = sum(acum_pesos.values())
total_ventas = sum(float(v["importe"]) for v in ventas_tab)
print(f"\n    Merma total del periodo: {total_pesos:,.0f} $ "
      f"({100 * total_pesos / total_ventas:.2f}% de las ventas)")
print(f"    Ventas registradas del periodo: {total_ventas:,.0f} $")

con.close()
print(f"\n[7] Base SQLite creada: {DB} "
      f"({DB.stat().st_size / 1024 / 1024:.1f} MB)")

# --------------------------------------------------------------------------
# Paso 7: clave de respuestas con los numeros MEDIDOS
# --------------------------------------------------------------------------
def fmt_pesos(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".") + " $"

lineas = [
    "# CLAVE DE RESPUESTAS — INVENTARIO DE BAR — NO ABRIR ANTES DE TERMINAR",
    "",
    "> Spoiler total. Usalo solo para autoevaluarte.",
    "",
    "## Números de control",
    "",
    "| Tabla | Filas |",
    "|---|---|",
]
for nombre in ["insumos", "carta", "recetas", "calendario", "ventas", "compras", "conteos"]:
    lineas.append(f"| `{nombre}` | {len(TABLAS[nombre][1])} |")

lineas += [
    "",
    f"- Periodo: **{N_SEMANAS} semanas** ({FECHA_INICIO} a {FECHA_INICIO + timedelta(days=N_DIAS - 1)})",
    f"- **{len(INSUMOS)} insumos**, **{len(CARTA)} tragos** en carta",
    f"- Merma total del periodo: **{fmt_pesos(total_pesos)}** "
    f"({100 * total_pesos / total_ventas:.2f}% de las ventas registradas)",
    f"- Ventas registradas: **{fmt_pesos(total_ventas)}**",
    "",
    "> ⚠️ **Ojo con el denominador.** El benchmark de la industria (1-2%) se mide sobre el",
    "> **valor del inventario**, no sobre las ventas. Acá se muestra sobre ventas porque es",
    "> lo que se puede calcular con estos datos. Calcularlo sobre el valor del inventario es",
    "> parte del ejercicio, y confundir los dos denominadores es un error profesional.",
    "",
    "---",
    "",
    "## Las 5 causas inyectadas",
    "",
    "| Cod | Causa | Dónde | Magnitud |",
    "|---|---|---|---|",
    f"| C1 | Over-pouring | Todos los insumos de coctelería | **+{(OVER_POUR - 1) * 100:.0f}%** sobre el uso teórico |",
    f"| C2 | Robo | {', '.join(f'`{k}`' for k in ROBO_POR_SEMANA)} | **{list(ROBO_POR_SEMANA.values())[0]} ml/semana** cada uno |",
    f"| C3 | Error de conteo | `{insumo_c3}`, semana {sem_c3} | **{env_c3} envases** de menos |",
    f"| C4 | Comp no registrado | `{trago_c4}`, semana {sem_c4} | **{comp_aplicado} tragos** sin cobrar |",
    f"| C5 | Remito no cargado | `{insumo_c5}`, semana {sem_c5} | **{env_c5} envases** entregados y no registrados |",
    "",
    "---",
    "",
    "## 🔑 El hallazgo que vale todo el ejercicio: ordená por PESOS, no por MILILITROS",
    "",
    "Así se ve la variación acumulada del periodo con las dos métricas:",
    "",
    "| # | Por mililitros (metrica ENGAÑOSA) | Por pesos (metrica CORRECTA) |",
    "|---|---|---|",
]
for k in range(5):
    n_ml, v_ml = top_ml[k]
    n_p, v_p = top_pesos[k]
    lineas.append(f"| {k + 1} | {n_ml} — {v_ml:,.0f} ml | **{n_p}** — {fmt_pesos(v_p)} |".replace(",", "."))

lineas += [
    "",
    "**Mirá la trampa.** Por mililitros, el ranking lo dominan *agua tónica, gaseosa cola y"
    " soda*: tienen un volumen enorme, así que un 6% de over-pouring produce más mililitros"
    " absolutos que medio litro de whisky robado por semana.",
    "",
    "**El robo no se busca por volumen, se busca por plata.** Un mixer de $2.100 el litro"
    "puede tener una variación enorme en ml y ser calderilla; un whisky premium de $42.600"
    "los 700 ml esconde seis cifras en un volumen mucho menor.",
    "",
    "> Esto es exactamente el tipo de error que comete un analista junior: ordena por la"
    "> métrica fácil (la que está en la columna obvia) en vez de por la métrica que le importa"
    "> al negocio. **Tu valor como analista está en elegir la métrica correcta.**",
    "",
    "---",
    "",
    "## 🔑 La segunda lección: cómo distinguir C3 de C4",
    "",
    "Las dos se ven como *un pico en una semana*. La diferencia está en **qué pasa la semana"
    "siguiente**:",
    "",
    "| | Semana anterior | **Semana del pico** | Semana siguiente | Firma |",
    "|---|---|---|---|---|",
    f"| **C3** error de conteo | +{var.get((insumo_c3, sem_c3 - 1), 0):,.0f} ml "
    f"| **+{var.get((insumo_c3, sem_c3), 0):,.0f} ml** "
    f"| **{var.get((insumo_c3, sem_c3 + 1), 0):,.0f} ml** "
    "| Par **+ / −**: el error se compensa |",
    f"| **C4** comp no registrado | +{var.get(('Ron blanco', sem_c4 - 1), 0):,.0f} ml "
    f"| **+{var.get(('Ron blanco', sem_c4), 0):,.0f} ml** "
    f"| +{var.get(('Ron blanco', sem_c4 + 1), 0):,.0f} ml "
    "| Pico **aislado**, sin compensación |",
]
lineas[-4:] = [l.replace(",", ".") for l in lineas[-4:]]

lineas += [
    "",
    "**Por qué:** si contás mal una semana, el error aparece como uso de más. Pero la semana"
    "siguiente partís del conteo bajo, así que el uso aparece de menos. **El error se"
    "compensa**, y el promedio de las dos semanas vuelve a la normalidad.",
    "",
    "Un comp no registrado no se compensa nunca: ese producto **se consumió de verdad** y"
    "nunca se registró la venta. El pico queda ahí para siempre.",
    "",
    "> **Consecuencia práctica:** ante un pico, mirá la semana siguiente. Si se compensa,"
    "> es un problema de conteo — y la acción es *recontar*, no *investigar un robo*.",
    "> Si no se compensa, ahí sí hay algo real que se consumió sin registrarse.",
    "",
    "---",
    "",
    "## 🔑 La tercera: variación positiva también es un problema",
    "",
    f"En `{insumo_c5}`, la semana {sem_c5} tiene una variación **negativa** de"
    f" **{var.get((insumo_c5, sem_c5), 0):,.0f} ml**: el uso registrado es *menor* que las"
    " ventas, lo cual es físicamente imposible.".replace(",", "."),
    "",
    "La causa es un **remito que llegó y no se cargó**: el stock subió, pero el sistema no"
    "lo sabe. Entonces el cálculo de uso resta un stock que nunca sumó, y da un número"
    "negativo.",
    "",
    "**Uso negativo = problema de registro, no de sustancia.** No se te perdió producto:"
    "te falta un papel. Es la primera cosa que hay que chequear antes de cualquier"
    "conclusión.",
    "",
    "---",
    "",
    "## ⚠️ La trampa de SQL que vas a encontrar",
    "",
    "Si escribís el reporte de variación así, te va a dar `NULL` en la primera semana de cada"
    "insumo:",
    "",
    "```sql",
    "-- MAL: WHERE se evalúa ANTES que las funciones de ventana",
    "SELECT LAG(cantidad) OVER (PARTITION BY id_insumo ORDER BY semana) AS previo",
    "FROM conteos",
    "WHERE semana > 0;   -- la fila de la semana 0 desaparece ANTES del LAG",
    "```",
    "",
    "`WHERE` se aplica antes que `LAG()`. Al filtrar la semana 0, la primera semana de cada"
    "insumo se queda sin fila anterior y el `LAG` devuelve `NULL`.",
    "",
    "**La solución es filtrar en una CTE exterior**, después de calcular la ventana (está en"
    "la consulta de abajo). Es un error que se comete en producción, en serio.",
    "",
    "---",
    "",
    "## Consultas de verificación",
    "",
    "```sql",
    VARIACION_SQL.strip() + ";",
    "```",
    "",
    "Con eso ya podés reconstruir las 5 causas. Las preguntas que siguen son el análisis:",
    "",
    "### Consulta 1 — ranking por pesos (debería dar los 3 SKU robados arriba)",
    "```sql",
    "-- Envolvé VARIACION_SQL en una CTE y agregá:",
    "SELECT nombre_insumo,",
    "       ROUND(SUM(variacion_ml), 0)    AS variacion_ml,",
    "       ROUND(SUM(variacion_pesos), 0) AS variacion_pesos",
    "FROM variacion",
    "GROUP BY nombre_insumo",
    "ORDER BY variacion_pesos DESC",
    "LIMIT 10;",
    "```",
    "",
    "### Consulta 2 — variación % sobre el teórico (para ver C1, el over-pouring parejo)",
    "```sql",
    "SELECT categoria,",
    "       ROUND(100.0 * SUM(variacion_ml) / NULLIF(SUM(uso_teorico_ml), 0), 1) AS variacion_pct",
    "FROM variacion",
    "GROUP BY categoria",
    "ORDER BY variacion_pct DESC;",
    "```",
    "",
    "### Consulta 3 — la serie semanal de un insumo (para ver el par +/- de C3)",
    "```sql",
    "SELECT semana, variacion_ml",
    "FROM variacion",
    "WHERE nombre_insumo = 'Ron blanco'",
    "ORDER BY semana;",
    "```",
    "",
    "---",
    "",
    "## Preguntas de negocio (sin respuesta única: son las de entrevista)",
    "",
    f"1. El over-pouring (C1) es **parejo y en todos los insumos**. ¿Qué acción toma un"
    " gerente con eso: capacitar, poner jigger obligatorio, o cambiar la receta?"
    " ¿Cuánto cuesta cada opción comparado con la merma?",
    f"2. Los 3 SKU robados son **de alto valor y fácil reventa**. ¿Cómo cambiarías el"
    " procedimiento de guardado sin acusar a nadie?",
    f"3. La variación de C3 se compensa y la de C4 no. Escribí el criterio en una frase"
    " para que otra persona pueda clasificar picos sin vos.",
    f"4. Si la merma total es {100 * total_pesos / total_ventas:.2f}% de las ventas,"
    " ¿cuánto es en un año? ¿Qué harías primero con ese número?",
    "5. ¿Qué dato te falta para calcular el pour cost de cada trago y compararlo con el"
    " ideal? ¿Qué cambiaría en el análisis si lo tuvieras?",
    "",
    "---",
    "",
    "## Archivos del dataset",
    "",
    "| Archivo | Qué es |",
    "|---|---|",
    "| `datos/bar/analisis_bar.db` | Base SQLite lista para abrir en DBeaver |",
    "| `datos/bar/*.csv` | Las 7 tablas en crudo (UTF-8 sin BOM) |",
    "| `datos/bar/BAR_CLAVE_NO_ABRIR.md` | Este archivo |",
    "",
]
RUTA_CLAVE = SALIDA / "BAR_CLAVE_NO_ABRIR.md"
RUTA_CLAVE.write_text("\n".join(lineas), encoding="utf-8")
print(f"[8] Clave de respuestas escrita: {RUTA_CLAVE}")

if fallos:
    print(f"\n[!] FALLOS DE VERIFICACION: {fallos}", file=sys.stderr)
    sys.exit(1)
print("\n[OK] El reporte de variacion recupera las 5 causas inyectadas.")
