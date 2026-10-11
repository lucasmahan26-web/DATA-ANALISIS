# Diagnóstico: qué datos tenés, qué se puede hacer, y cómo no meterte en problemas

> Dos cosas antes de tocar nada: **(1)** el protocolo de autorización, porque son datos de tu
> empleador y no son tuyos; **(2)** el diagnóstico, que es lo que define qué análisis podés
> hacer. Empezá por el punto 1.

---

# PARTE 1 — Autorización y anonimización

## Lo que tenés entre manos no es un dataset cualquiera

El inventario de un bar contiene información **comercialmente sensible**:

| Dato | Por qué es sensible |
|---|---|
| Precios de compra | Un competidor deduce tus márgenes y tu poder de negociación |
| Nombres de proveedores | Son relaciones comerciales del dueño, no tuyas |
| **Recetas** | Son la propiedad intelectual del bar. Una receta filtrada es un activo perdido |
| Ventas totales | Información financiera privada |
| Nombres de compañeros | Datos personales |

Publicar esto sin permiso no es un problema de portafolio: es un problema laboral y
potencialmente legal. **Pero tiene solución, y la solución además te conviene.**

## El orden correcto (y por qué te conviene)

El error sería: *"jefe, quiero usar el inventario para mi portafolio"*. Eso es pedir un favor
por adelantado y suena a que vas a hacer algo para vos con sus datos.

La secuencia que funciona:

```
1. Hacé el análisis PARA EL BAR, en tu trabajo, sin publicar nada.
   Esto no requiere permiso especial: es tu trabajo, con datos de tu trabajo.

2. Mostrale los hallazgos a tu jefe.
   "Encontré que hay $X de variación sin explicar en estos 4 insumos."

3. AHORA pedí permiso para publicar una versión anonimizada.
   Ya diste valor. Estás pidiendo algo después de haber aportado.
```

Fijate que **esto es exactamente la conversación de transferencia interna** del
playbook de búsqueda laboral (en tus notas personales, no publicado).
No son dos cosas: es la misma.
Tu "proceso manual doloroso" ya lo encontraste — es el control de inventario del bar.

## Qué preguntarle a tu jefe (texto sugerido)

> *"Estuve analizando el inventario y encontré algunas cosas interesantes — por ejemplo, hay
> diferencias entre lo que deberíamos haber consumido y lo que consumimos. ¿Te interesa que te
> lo muestre?*
>
> *Aparte: me gustaría usar los datos para un proyecto de portafolio. Sería una versión
> anonimizada — sin nombres de proveedores, sin precios reales, sin recetas, y con los productos
> como 'Insumo A', 'Insumo B'. Solo porcentajes y comparaciones. ¿Te parece bien?"*

**Pedí las dos cosas juntas pero en ese orden.** Primero el valor, después el pedido.

## Los 3 niveles de anonimización

| Nivel | Qué publicás | Riesgo | ¿Sirve para el portafolio? |
|---|---|---|---|
| **1 — Recomendado** | Estructura, porcentajes, índices (base 100), nombres genéricos | Nulo | **Sí, perfectamente** |
| **2 — Aceptable** | Todo agregado por categoría, sin detalle por producto | Bajo | Sí, un poco menos rico |
| **3 — No hagas** | Precios reales, proveedores, recetas, ventas reales | Alto | No vale el riesgo |

**El truco que preserva el valor analítico sin revelar nada:** publicá **ratios e índices**.
"El Insumo A representa el 38% del valor del inventario" dice todo lo que un reclutador necesita
saber, y no revela nada comercial. Lo mismo con "el pour cost bajó de 26% a 23%": el porcentaje
es el hallazgo, el precio no aporta nada.

## Cómo me lo mandás a mí también

Aunque yo sea una IA, **no me pegues los datos reales de tu empleador** (precios, proveedores,
ventas, recetas). No por desconfianza: es la misma disciplina que vas a necesitar en cualquier
empresa, y es la que te va a hacer ver profesional.

Mandame esto:

- ✅ Los **nombres de las columnas** de tu planilla (tal cual están)
- ✅ **2 o 3 filas de ejemplo con valores inventados**
- ✅ Cantidades aproximadas: "unos 80 insumos", "conteos semanales desde marzo"
- ✅ Qué tipo de bar es y cuántos días abre
- ❌ Precios reales, nombres de proveedores, recetas, ventas reales

Con eso te armo un dataset sintético con la forma exacta del tuyo, para que practiques las
técnicas antes de aplicarlas a los datos reales.

**Plan B si tu jefe dice no:** el proyecto se hace igual con datos sintéticos que repliquen la
estructura. El portafolio dice *"análisis de control de inventario de un bar"* y no *"análisis
de datos de mi empleador"*. Perdés poco y no arriesgás nada.

---

# PARTE 2 — El diagnóstico

Andá a mirar tu inventario y marcá lo que tengas. **No importa que falte casi todo:** el
diagnóstico está armado para que sepas qué podés hacer con lo que hay.

## Bloque 1 — El inventario

- [ ] Está en **Excel / planilla**
- [ ] Está en **papel** (o foto de papel)
- [ ] Está en un **sistema o app** (¿cuál? ____________)
- [ ] Tiene **más de un conteo en el tiempo** (fechas distintas) ← *esto es clave*
- [ ] Tiene **solo un conteo** (una foto del momento)
- [ ] Tiene **costo unitario** o precio de compra por producto
- [ ] Tiene **cantidades contadas** por producto
- [ ] Tiene **categorías** (destilados, cervezas, vinos, insumos, descartables…)
- [ ] Tiene **stock mínimo / par level** o punto de pedido
- [ ] Tiene **unidad de medida** por producto (botella, ml, kg, caja)
- [ ] Las unidades están **mezcladas** o son inconsistentes
- [ ] Aproximadamente cuántos productos: ______

## Bloque 2 — Ventas

- [ ] Tengo acceso al **POS** (¿cuál? ____________)
- [ ] Puedo exportar **ventas por producto** (unidades por trago/artículo)
- [ ] Solo puedo ver el **total del día** (sin detalle)
- [ ] El POS **registra comps / invitaciones / bebidas sin cobrar**
- [ ] Puedo sacar ventas **por turno**
- [ ] No tengo acceso a ventas

## Bloque 3 — Compras

- [ ] Hay **remitos o facturas** de proveedores
- [ ] Los remitos tienen **precios**
- [ ] Están **digitalizados** (Excel, PDF, sistema)
- [ ] Están **en papel** (carpeta, caja)
- [ ] No hay registro de compras

## Bloque 4 — Recetas

- [ ] Existen **recetas estandarizadas** con cantidades
- [ ] Las recetas están **escritas** en algún lado
- [ ] Las recetas están **solo de memoria** (las sabe el equipo)
- [ ] No hay recetas estandarizadas

## Bloque 5 — Operación

- [ ] Cuántos días por semana abren: ______
- [ ] Cuántos turnos por día: ______
- [ ] Cada cuánto se hace el conteo de inventario: ______
- [ ] Quién lo hace: ______
- [ ] Cuántas personas trabajan en la barra: ______
- [ ] Tipo de bar (tragos / cervecería / restaurante con barra / boliche / hotel): ______

---

## PARTE 3 — Qué habilita cada cosa (el árbol de decisión)

Buscá tu fila y sabé de antemano qué proyecto podés construir. **Cada nivel es un proyecto
publicable**, así que no importa si te falta lo de abajo.

| Si tenés… | Podés hacer | Nivel |
|---|---|---|
| Solo un conteo con cantidades | Clasificación de productos, conteo de referencias, estructura de la carta | 🟢 Base |
| Un conteo **+ costos** | **Valorización del inventario, análisis ABC**, capital inmovilizado | 🟢 Base+ |
| Conteos **en varias fechas** | Consumo por período, rotación de inventario, quiebres de stock | 🟡 Intermedio |
| + costos + varias fechas | Rotación por valor, tendencia de consumo, detección de deterioro | 🟡 Intermedio |
| + **ventas totales** | **Pour cost global**, evolución del costo de venta | 🟠 Avanzado |
| + **ventas por producto** | Mix de ventas, patrones por día/turno, **estacionalidad**, quiebres estimados | 🟠 Avanzado |
| + **recetas** | Costo por trago, **ingeniería de menú (Kasavana & Smith)** | 🔴 Alto |
| + recetas + ventas por producto + conteos | **REPORTE DE VARIACIÓN** ← el análisis estrella | 🔴 Alto |

**El reporte de variación es la meta.** No es el punto de partida, y no pasa nada: el camino
hacia ahí ya es un portafolio completo.

> **Casi seguro tenés el nivel 🟢 o 🟡 sin darte cuenta.** Un Excel con productos, cantidades y
> costos ya alcanza para un proyecto con ABC y valorización, que **la mayoría de los bares nunca
> hizo**. Eso es un proyecto de portafolio real.

---

## Lo que necesito que me traigas

Copiá esto y completalo. Con eso armo el dataset sintético con la forma de tu planilla y el plan
de análisis concreto.

```
TIPO DE BAR:
DÍAS QUE ABREN:
CONTEOS (cuántos y cada cuánto):
FORMATO DEL INVENTARIO (Excel / papel / sistema):

COLUMNAS DE MI PLANILLA (tal cual están escritas):
  1.
  2.
  3.
  ...

2 O 3 FILAS DE EJEMPLO (con valores INVENTADOS):
  ...

CANTIDAD APROXIMADA DE PRODUCTOS:
¿TENGO VENTAS POR PRODUCTO? (sí / no / no sé):
¿TENGO RECETAS ESCRITAS? (sí / no / parcialmente):
¿TENGO REMITOS CON PRECIOS? (sí / no / parcialmente):
```

---

## Y no te olvides: esto ya es tu conversación con tu jefe

Fijate que no tenés que "buscar un proceso manual" para el playbook: **ya lo encontraste**.
El control de inventario del bar es tu proceso manual, tu Proyecto 4 y tu audición interna,
todo en el mismo lugar.

Y tenés una ventaja que ningún otro candidato tiene: **sabés cómo funciona la barra por
dentro.** Sabés qué es un par level, por qué se rompe una botella, qué pasa un viernes a la
noche, por qué el conteo de las 3 AM no es confiable. Eso no se estudia: se vive.

Eso es exactamente lo que un analista de datos tiene que tener y lo que casi ningún junior
tiene.
