# Especificación de la capa `marts` — Proyecto 2

> **Qué es esto:** la definición de las vistas de negocio que produce tu `02_marts.sql`.
> Define **estructura** (grano, columnas, qué responde cada vista). Las **decisiones de
> negocio** (qué hacer con los huérfanos, las devoluciones, los duplicados) las tomás vos
> y las documentás — eso es tu trabajo, y es lo que se evalúa.

---

## Por qué existe una capa `marts` (y no consultás las tablas crudas)

Podrías responder las 10 preguntas escribiendo consultas directas sobre `ventas`. Y tendrías
10 definiciones distintas de "venta neta", cada una con sus propios filtros.

El problema aparece a los dos meses, cuando el gerente pregunta *"¿por qué el total de este
reporte no coincide con el del mes pasado?"*. Y la respuesta es: *"porque son dos consultas
distintas"*. Eso es un problema de arquitectura, no de SQL.

**La capa `marts` resuelve eso:** define el número **una vez**, en un lugar, con las reglas
de negocio escritas. Todas las preguntas se responden *sobre* esa definición.

```
tablas crudas  →  staging (limpieza)  →  marts (negocio)  →  análisis (las 10 preguntas)
  ventas            stg_ventas            mart_ventas_*       03_analisis.sql
  productos         stg_productos         mart_clientes
  ...               ...                   mart_calidad
```

| Capa | Qué contiene | Archivo |
|---|---|---|
| **Cruda** | Lo que exportó el sistema, con sus 15 defectos | ya cargada |
| **Staging** | Los mismos datos, limpios y tipados. **Tu limpieza va acá** | `01_staging.sql` |
| **Marts** | Vistas de negocio con las métricas definidas una sola vez | `02_marts.sql` |
| **Análisis** | Las 10 preguntas, respondidas sobre los marts | `03_analisis.sql` |

> **La regla que hace la diferencia:** en `03_analisis.sql` **no debería haber ningún `JOIN`
> a las tablas crudas ni ningún `WHERE` de limpieza**. Solo `SELECT ... FROM mart_...`.
> Si tu análisis necesita filtrar basura, esa basura debería estar resuelta en staging.

---

## Las 4 vistas

### 1 · `mart_ventas_mes` — la vista base

**Grano:** un registro por **mes × sucursal × categoría**.
**Responde:** evolución mensual, comparación entre sucursales, mix por categoría.
**Fuentes:** `ventas` + `sucursales` + `productos` + `categorias`

| Columna | Tipo | Definición de negocio |
|---|---|---|
| `anio` | int | Año de la venta |
| `mes` | int | Mes (1–12) |
| `periodo` | text | `'2024-03'`, para ordenar y mostrar |
| `id_sucursal` | int | Sucursal |
| `nombre_sucursal` | text | Nombre legible |
| `region` | text | Región de la sucursal |
| `id_categoria` | int | Categoría del producto |
| `nombre_categoria` | text | Nombre legible |
| `pedidos` | int | Cantidad de `id_pedido` **distintos** |
| `lineas` | int | Cantidad de líneas de venta |
| `unidades` | int | Suma de `cantidad` |
| `venta_neta` | numeric | Suma de `importe_neto` **recalculado** |
| `ticket_promedio` | numeric | `venta_neta / pedidos` |
| `descuento_promedio` | numeric | `AVG(descuento)` |

**Preguntas que habilita:** 1 (evolución mensual), 3 (sucursales), 8 (participación por categoría).

> **Decisión tuya, y va escrita en el README:** ¿`venta_neta` incluye las devoluciones
> (cantidades negativas)? ¿Las excluye? ¿Las muestra aparte? Las tres son defendibles.
> Lo indefendible es no haberlo decidido.

---

### 2 · `mart_productos` — rentabilidad y rotación

**Grano:** un registro por **producto × mes**.
**Responde:** qué se vende, qué deja plata, qué está muerto.
**Fuentes:** `ventas` + `productos` + `categorias`

| Columna | Tipo | Definición de negocio |
|---|---|---|
| `id_producto` | int | Producto |
| `nombre_producto` | text | Nombre legible |
| `nombre_categoria` | text | Categoría |
| `activo` | text | `S` / `N` según el maestro |
| `periodo` | text | `'2024-03'` |
| `unidades` | int | Suma de `cantidad` |
| `venta_neta` | numeric | Suma de `importe_neto` recalculado |
| `precio_promedio` | numeric | `venta_neta / NULLIF(unidades, 0)` |
| `participacion_pct` | numeric | `venta_neta / SUM(venta_neta) OVER (PARTITION BY periodo) * 100` |
| `ranking_periodo` | int | `RANK()` por `venta_neta` dentro del período |
| `participacion_acum` | numeric | Suma acumulada de `participacion_pct` (para el **análisis ABC**) |

**Preguntas que habilita:** 2 (top productos), 7 (productos sin ventas en 90 días), y el
análisis ABC (Pareto) que no está en la lista de 10 pero suma.

> **Ojo con `ranking_periodo`:** si dos productos empatan, `RANK()` les da la misma posición
> y salta el siguiente número. `ROW_NUMBER()` no empata nunca pero elige arbitrariamente.
> **Elegí uno y decí por qué.** Es una pregunta de entrevista segura.

---

### 3 · `mart_vendedores` — desempeño

**Grano:** un registro por **vendedor × período**.
**Responde:** quién vende más, y **dentro de qué sucursal**.
**Fuentes:** `ventas` + `vendedores` + `sucursales`

| Columna | Tipo | Definición de negocio |
|---|---|---|
| `id_vendedor` | int | Vendedor |
| `nombre_vendedor` | text | Nombre legible |
| `id_sucursal` | int | Sucursal del vendedor |
| `nombre_sucursal` | text | Nombre legible |
| `turno` | text | Turno |
| `periodo` | text | `'2024-03'` |
| `pedidos` | int | Pedidos distintos |
| `venta_neta` | numeric | Suma de `importe_neto` recalculado |
| `ticket_promedio` | numeric | `venta_neta / pedidos` |
| `ranking_en_sucursal` | int | Posición **dentro de su sucursal** (`PARTITION BY`) |

**Preguntas que habilita:** 4 (ranking de vendedores).

> **El punto fino:** `ranking_en_sucursal` usa `PARTITION BY id_sucursal`. Un ranking global
> sería engañoso: un vendedor de una sucursal chica nunca va a competir con uno de la
> sucursal grande. **Ese es el tipo de decisión que demuestra criterio de negocio**, no de SQL.

---

### 4 · `mart_clientes` — comportamiento y retención

**Grano:** un registro por **cliente** (sin período: es una foto acumulada).
**Responde:** quién compra, quién se fue, cada cuánto compra.
**Fuentes:** `ventas` + `clientes`

| Columna | Tipo | Definición de negocio |
|---|---|---|
| `id_cliente` | int | Cliente |
| `razon_social` | text | Nombre legible |
| `tipo_cliente` | text | Consumidor Final / Mayorista / Empresa / Corporativo |
| `ciudad`, `provincia` | text | Ubicación |
| `primera_compra` | date | `MIN(fecha_venta)` |
| `ultima_compra` | date | `MAX(fecha_venta)` |
| `pedidos` | int | Pedidos distintos |
| `venta_neta` | numeric | Suma acumulada |
| `ticket_promedio` | numeric | `venta_neta / pedidos` |
| `dias_desde_ultima_compra` | int | Días desde `ultima_compra` hasta el cierre del dataset |
| `compro_2023` | bool | Compró al menos una vez en 2023 |
| `compro_2024` | bool | Compró al menos una vez en 2024 |
| `dias_entre_compras` | numeric | Promedio de días entre compras consecutivas (`LAG`) |

**Preguntas que habilita:** 5 (ticket por tipo de cliente), 6 (churn 2023→2024),
9 (tiempo entre compras).

> **`dias_desde_ultima_compra` necesita una fecha de referencia.** ¿La fecha máxima del
> dataset, o la fecha de hoy? Si usás `CURRENT_DATE`, el número **cambia todos los días** y
> tu análisis deja de ser reproducible. **Usá la fecha máxima del dataset** y escribilo.
> Un análisis que da un resultado distinto cada vez que lo corrés no es un análisis.

---

### 5 · `mart_calidad_datos` — el que casi nadie construye

**Grano:** un registro por **chequeo**.
**Responde:** qué problemas tenía el dato crudo, cuántos, y qué se hizo con cada uno.
**Fuentes:** todas las tablas — es el mart transversal.

| Columna | Tipo | Definición de negocio |
|---|---|---|
| `chequeo` | text | Nombre del control (ej. `'id_venta duplicado'`) |
| `tabla` | text | Dónde se detectó |
| `filas_afectadas` | int | Cuántas |
| `accion` | text | `'excluida'` / `'corregida'` / `'conservada'` / `'separada'` |
| `justificacion` | text | Por qué esa acción |

**Preguntas que habilita:** todas, indirectamente.

> **Este es el mart que más te va a diferenciar en una entrevista.** Cualquiera hace un
> dashboard de ventas. Casi nadie puede mostrar, con números, qué problemas tenía el dato y
> qué decidió con cada uno. Y la columna `justificacion` es la que convierte un conteo en
> criterio profesional.

---

## Cobertura: qué mart responde cada pregunta

| # | Pregunta del README | Mart |
|---|---|---|
| 1 | Ventas netas por mes y variación MoM | `mart_ventas_mes` |
| 2 | Top 10 productos por ventas netas | `mart_productos` |
| 3 | Sucursales: evolución y comparación | `mart_ventas_mes` |
| 4 | Ranking de vendedores por sucursal | `mart_vendedores` |
| 5 | Ticket promedio por tipo de cliente | `mart_clientes` |
| 6 | Clientes de 2023 que no compraron en 2024 | `mart_clientes` |
| 7 | Productos sin ventas en los últimos 90 días | `mart_productos` |
| 8 | Participación % de cada categoría | `mart_ventas_mes` |
| 9 | Tiempo entre compras por cliente | `mart_clientes` |
| 10 | Sucursales con caída interanual | `mart_ventas_mes` |

**Cobertura completa: las 10 preguntas se responden con 4 marts y ningún `JOIN` a las tablas
crudas.** Si tu `03_analisis.sql` necesita un `JOIN` extra, es señal de que falta una columna
en un mart.

> ### La tabla que queda sin usar: `medios_pago`
>
> Ninguno de los 4 marts la expone. **Ninguna de las 10 preguntas pregunta por medio de pago**,
> así que no es un error — pero es una decisión, y conviene que la veas:
>
> - Si quisieras responder *"¿qué porcentaje se cobra con tarjeta?"*, tendrías que agregar
>   `id_medio_pago` al grano de `mart_ventas_mes`. **Eso multiplica las filas** por cada medio
>   de pago, y cualquier `SUM(venta_neta)` sobre ese mart seguiría dando el total (porque las
>   filas se reparten, no se duplican), pero un `COUNT(*)` de pedidos pasaría a contar mal.
> - Es el ejemplo perfecto de por qué **el grano de un mart es una decisión de negocio**: la
>   misma tabla sirve para una pregunta y arruina otra.
>
> **Tarea:** cuando definas tus marts, escribí en el README qué tablas del modelo quedaron
> afuera y por qué. Una tabla sin usar no es un olvido si está justificada.

---

## Las 5 decisiones que tenés que tomar y documentar

La especificación te da la estructura. Estas cinco cosas **no** te las resuelvo yo, porque son
el ejercicio del Proyecto 2:

1. **Devoluciones** (cantidades negativas): ¿entran en `venta_neta` o van aparte?
2. **Registros huérfanos** (producto/sucursal/vendedor/cliente que no existe en el maestro):
   ¿se excluyen de los marts, o se agrupan en una fila "Sin asignar"?
3. **Duplicados de `id_venta`**: ¿cuál de las dos versiones gana? ¿O se suman?
4. **Importes inconsistentes**: ¿usás el `importe_neto` del sistema o el recalculado?
   (Pista: el recalculado, pero **tenés que decir por qué**).
5. **Clientes con `id_cliente` duplicado**: ¿son el mismo cliente o dos sucursales del mismo?
   Cambia por completo el cálculo de retención.

Para cada una: **la decisión, el número que la respalda, y qué pasaría si eligieras la otra
opción.** Eso último es lo que separa "decidí esto" de "entendí el problema".
