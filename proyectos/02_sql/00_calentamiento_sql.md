# Calentamiento SQL — 28 ejercicios sobre la base `analisis.db`

> **Objetivo:** soltura de sintaxis. Esto NO es el diagnóstico del Proyecto 2.
> Acá practicás las cláusulas; el diagnóstico de los 15 defectos es otra cosa
> (está en el [README del proyecto](README.md)).
>
> Estos ejercicios **no tienen la respuesta escrita a propósito**. La forma de
> saber si acertaste es mirar el resultado y preguntarte *"¿tiene sentido?"*.

---

## Cómo abrir la base en DBeaver (5 minutos, sin instalar nada)

Tenés DBeaver, así que ya está casi todo hecho. DBeaver no trae una base de datos:
es solo el cliente. Por eso te dejé la base ya armada en `datos/p2/analisis.db`.

1. Abrí DBeaver.
2. **Database → New Database Connection** (o el ícono del enchufe con `+`).
3. Elegí **SQLite** → *Next*.
4. En **Path**, botón *Browse* → navegá hasta `datos/p2/analisis.db` → *Open*.
5. *Test Connection* (si pide driver, aceptá la descarga) → *Finish*.
6. En el panel izquierdo vas a ver `analisis.db` → desplegá → `Tables` → las 7 tablas.

**Atajos que te van a ahorrar horas:**

| Atajo | Qué hace |
|---|---|
| `Ctrl + Enter` | Ejecuta **solo** la consulta donde está el cursor |
| `Ctrl + Shift + Enter` | Ejecuta todo el script |
| `Alt + X` | Ejecuta solo la línea seleccionada |
| `Ctrl + Espacio` | Autocompletado de tablas y columnas |
| Doble clic en una tabla | Muestra la estructura y los datos |

**Regla de oro:** terminá siempre tus consultas de exploración con `LIMIT 100`.
Sin eso, DBeaver intenta traer 130.000 filas y se te cuelga la máquina.

**El error que vas a cometer:** ejecutar todo el script con `Ctrl+Enter` cuando solo
querías probar una parte. Si te da un resultado raro, seleccioná la consulta y
volvé a ejecutar.

---

## ⚙️ SQLite o PostgreSQL: los dos sirven, y hay 4 ejercicios que cambian

Los ejercicios están escritos en dialecto **SQLite** porque la base de práctica
(`analisis.db`) es SQLite y no requiere configuración. Pero **tenés PostgreSQL 18
instalado y corriendo**, así que podés hacerlos ahí también — y conviene, porque es el
motor que piden las ofertas.

**27 de los 28 ejercicios son SQL estándar y corren igual en los dos motores.** Solo
cambian **4**, y todos por lo mismo: las funciones de fecha.

| Ejercicio | SQLite | PostgreSQL |
|---|---|---|
| 14 | `strftime('%Y', fecha)` / `strftime('%m', fecha)` | `EXTRACT(YEAR FROM fecha)` / `EXTRACT(MONTH FROM fecha)` |
| 26, 27, 28 | `strftime('%Y-%m', fecha)` | `TO_CHAR(fecha, 'YYYY-MM')` |

**Verificado, no supuesto:** los 28 ejercicios en dialecto PostgreSQL ejecutan sin error
contra PostgreSQL 18, y el control confirma que el dialecto SQLite **falla**:

```
ERROR:  function strftime(unknown, date) does not exist
```

> Eso es exactamente por lo que no podés copiar y pegar SQL entre motores sin entenderlo.
> El error es claro y aparece enseguida — pero hay diferencias que **no** dan error y
> devuelven un número distinto. Esas son las peligrosas, y las vas a ver en el Proyecto 2.

**Tenés la versión PostgreSQL de los 28 ejercicios lista para correr** en
`datos/p2/calentamiento_postgres.sql`. Y podés verificar todo de una con:

```powershell
.\scripts\verificar_postgres.ps1
```

Levanta un clúster temporal, carga los datos, corre los 28 ejercicios, prueba el DDL y las
constraints, y borra todo. **No toca tu base de datos.**

---

## El modelo (tenelo a mano)

```
categorias(id_categoria, nombre_categoria, departamento)
productos(id_producto, nombre_producto, id_categoria, precio_lista, activo, fecha_alta)
sucursales(id_sucursal, nombre_sucursal, region, provincia, zona_comercial, fecha_apertura)
vendedores(id_vendedor, nombre_vendedor, id_sucursal, fecha_ingreso, turno)
clientes(id_cliente, razon_social, tipo_cliente, ciudad, provincia, fecha_alta)
medios_pago(id_medio_pago, descripcion)
ventas(id_venta, id_pedido, fecha_venta, id_producto, id_sucursal, id_vendedor,
       id_cliente, id_medio_pago, cantidad, precio_unitario, descuento, importe_neto)
```

`ventas` es la tabla grande (130.688 filas). Las demás son chicas.

> ### ⚠️ Ojo: los datos están sucios A PROPÓSITO
>
> Este dataset tiene 15 defectos inyectados, así que vas a ver cosas raras
> mientras practicás. **No son errores tuyos.** Por ejemplo:
>
> - Vas a encontrar ventas del año **1900** y del **2030**.
> - Vas a ver `importe_neto` **negativos**.
> - Vas a ver productos y sucursales que **no existen** en las tablas de dimensión.
> - El ejercicio 24 te va a dar **dos conteos distintos** de la misma tabla: eso es
>   exactamente el fenómeno que vas a investigar en el Proyecto 2.
>
> Para el calentamiento: **ignoralo y seguí practicando sintaxis.** Encontrar y
> arreglar esas cosas es el Proyecto 2, no el calentamiento.

---

## Bloque 1 — Lo básico (SELECT, WHERE, ORDER BY, LIMIT)

**1.** Mostrá las primeras 20 filas de `ventas`.

**2.** Traé solo `id_venta`, `fecha_venta` e `importe_neto`.

**3.** Las 10 ventas con mayor `importe_neto`.
> *Cláusulas:* `ORDER BY ... DESC LIMIT 10`

**4.** Las ventas del 15 de marzo de 2024.
> *Pista:* las fechas están como texto en formato `YYYY-MM-DD`, así que
> `WHERE fecha_venta = '2024-03-15'` funciona.

**5.** Las ventas con `importe_neto` mayor a 50.000, ordenadas de mayor a menor.
> *Dato útil:* solo unas 4.600 filas superan ese umbral. Si te devuelve 0 resultados,
> tu operador de comparación está al revés.

**6.** Las ventas de marzo de 2024 (el mes entero, no un día).
> *Pista:* `BETWEEN` o comparación de texto. Las fechas como texto se comparan
> alfabéticamente y para ISO eso **coincide** con el orden cronológico.

**7.** ¿Cuántos medios de pago hay y cuáles son? (tabla `medios_pago`)

**8.** Los productos que están inactivos (`activo = 'N'`).

---

## Bloque 2 — Agregaciones (COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING)

**9.** ¿Cuántas filas tiene `ventas` en total?

**10.** ¿Cuál es la suma total de `importe_neto` de toda la tabla?
> Ojo: todavía no limpiaste. Este número va a cambiar cuando saques duplicados
> y huérfanos. Anotalo: es tu "antes".

**11.** ¿Cuál es el `importe_neto` promedio, mínimo y máximo? Redondeá con `ROUND(x, 2)`.

**12.** Contá cuántas ventas hay por `turno` de vendedor.
> *Necesitás:* `JOIN` con `vendedores` + `GROUP BY`

**13.** Cantidad de ventas por `region` de sucursal.
> *Necesitás:* `JOIN` con `sucursales` + `GROUP BY`

**14.** Suma de `importe_neto` por `anio` y `mes`.
> *Pista:* en SQLite, `strftime('%Y', fecha_venta)` y `strftime('%m', fecha_venta)`.
> En PostgreSQL sería `EXTRACT(YEAR FROM fecha_venta)` / `DATE_TRUNC('month', ...)`.

**15.** Los 5 productos (por `id_producto`) con mayor cantidad de unidades vendidas,
ordenados de mayor a menor.
> *Cláusulas:* `GROUP BY` + `SUM(cantidad)` + `ORDER BY ... DESC LIMIT 5`

**16.** Los `tipo_cliente` que tienen más de 200 ventas registradas.
> **Esta es la pregunta clave del bloque.** Si filtrás con `WHERE` te va a dar error
> de sintaxis o un resultado incorrecto: el filtro sobre una agregación va en `HAVING`.
> La diferencia entre `WHERE` y `HAVING` es una de las preguntas más frecuentes de
> entrevista, y la vas a entender de verdad acá.

**17.** ¿Cuántos pedidos distintos (`id_pedido`) hay? Comparalo con la cantidad de
filas de `ventas`. ¿Por qué son distintos?
> *Usá:* `COUNT(DISTINCT id_pedido)`

---

## Bloque 3 — Filtrar con criterio (DISTINCT, IN, BETWEEN, LIKE, CASE)

**18.** Listá las `region` distintas de `sucursales`, sin repetidos.

**19.** Las ventas cuyo `id_medio_pago` sea 1 o 5.
> *Hacelo dos veces:* con `OR` y con `IN`. ¿Cuál se lee mejor?

**20.** Los productos cuyo nombre contenga "Leche".
> *Usá:* `LIKE '%Leche%'`
> **Ojo con esto:** ¿cuántos resultados te dio? ¿Todos son leche? Este tipo de
> búsqueda por texto es la que después te hace falta para encontrar categorías
> mal escritas.

**21.** Clasificá cada venta en su rango de importe, en una columna nueva:
`'chico'` si `importe_neto < 10000`, `'mediano'` si está entre 10.000 y 50.000,
`'grande'` si supera 50.000. Mostrá cuántas ventas hay de cada rango.
> *Usá:* `CASE WHEN ... THEN ... ELSE ... END`
> *Dato útil:* los tres rangos tienen que tener ventas. Si alguno te da 0, revisá
> los límites de tu `CASE`.

---

## Bloque 4 — JOINs (la parte que más se evalúa)

**22.** Mostrá `id_venta`, `fecha_venta`, `nombre_producto` y `importe_neto` de las
primeras 50 ventas.
> *Necesitás:* `JOIN productos ON ventas.id_producto = productos.id_producto`

**23.** Sumá `importe_neto` por `nombre_categoria`.
> *Necesitás:* tres tablas encadenadas: `ventas` → `productos` → `categorias`.

**24.** Mostrá todas las ventas con el nombre de la sucursal, **incluyendo** las que
no tienen sucursal asignada.
> **Acá está el ejercicio más importante de todos.**
>
> Hacelo primero con `JOIN` (o sea `INNER JOIN`) y contá las filas.
> Después hacelo con `LEFT JOIN` y volvé a contar.
>
> **La diferencia entre esos dos números es la respuesta a la pregunta más
> frecuente de las entrevistas técnicas de SQL.** Cuando la entiendas, no la vas
> a olvidar más. ¿Cuál de los dos te sirve para encontrar los registros huérfanos?

---

## Bloque 5 — Cuando ya te salga todo lo anterior

Estos son los que te llevan al nivel que piden las ofertas. Todavía no los necesitás
si el bloque 4 te cuesta.

**25.** Listá los vendedores con sus ventas totales, **incluyendo los que no
vendieron nada** (mostrarían 0 o NULL). ¿Cómo distinguís "no vendió nada" de
"no existe"?

**26.** Para cada sucursal, mostrá su mes con mayor facturación.
> *Pista:* una CTE (`WITH`) que agregue por sucursal y mes, y después elegir el máximo.
> *Técnica:* `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`

**27.** La variación porcentual de facturación mes a mes.
> *Usá:* `LAG(importe) OVER (ORDER BY mes)`

**28.** El acumulado del año (running total) de facturación por mes.
> *Usá:* `SUM(...) OVER (ORDER BY mes ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

> **Si los window functions te dan error de sintaxis**, tu driver SQLite es viejo
> (necesitás 3.25+). No es tu culpa: pasá a PostgreSQL y volvé a intentarlo.

---

## Cómo saber si tu respuesta está bien (sin la clave)

No hay una única forma de escribir una consulta, así que no te doy "la" respuesta.
Usá estas tres técnicas de autoverificación:

1. **Contá antes de creer.** Si tu consulta dice que hay 3 sucursales con ventas,
   hacé una consulta aparte que cuente las filas a mano y comparé.
2. **Buscá el caso extremo.** Ordená por el valor y mirá el primero y el último.
   Si el máximo es absurdo, probablemente tu JOIN duplicó filas.
3. **Preguntate si el número tiene sentido de negocio.** Un ticket promedio de
   3.000.000 o de 2 pesos probablemente sea un error tuyo, no del negocio.

**El error de JOIN más común:** cuando la relación es 1 a muchos y juntás dos tablas
"muchas", las filas se multiplican y tu suma queda inflada. Si un total te da más
grande de lo que esperabas, casi siempre es esto: revisá con `COUNT(*)` antes y
después del JOIN.

---

## Progreso

- [ ] Bloque 1 (1–8) — sin mirar nada
- [ ] Bloque 2 (9–17) — entiendo `WHERE` vs `HAVING`
- [ ] Bloque 3 (18–21) — `CASE WHEN` me sale solo
- [ ] Bloque 4 (22–24) — entiendo `INNER` vs `LEFT JOIN` de verdad
- [ ] Bloque 5 (25–28) — window functions

Cuando cierres el bloque 4, ya estás listo para el diagnóstico del Proyecto 2.
