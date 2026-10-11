# De SQL a DAX: la traducción, patrón por patrón

> **Este documento existe por una razón concreta:** si ya sabés SQL, el 90% de DAX
> no es sintaxis nueva, es **el mismo patrón con otro nombre**. Lo que sí es nuevo
> —y es lo que traba a todo el mundo— es un cambio de modelo mental que se explica
> en la primera sección.
>
> **Verificación:** los 12 ejemplos SQL de esta guía están ejecutados y verificados
> contra `datos/bar/analisis_bar.db` (ver `scripts/verificar_sql_a_dax.py`). Los números
> que ves son los que devuelve la base.
>
> ⚠️ **Lo que NO está verificado: la sintaxis DAX.** No se puede ejecutar DAX sin Power BI
> Desktop. Está escrita siguiendo las reglas del lenguaje, pero la verificación final la
> tenés que hacer vos cargando el modelo. Al final del documento hay un procedimiento
> concreto para hacerlo en 10 minutos.

---

## Parte 1 · El cambio de modelo mental (esto es lo difícil)

### SQL describe un resultado. DAX define un valor.

En SQL escribís una consulta y obtenés **una respuesta fija**:

```sql
SELECT SUM(importe) FROM ventas;   -- 253.648.500. Siempre.
```

En DAX definís una **medida**, que es una fórmula sin valor propio. Su valor depende
del **contexto de filtro** en el momento en que se dibuja:

```dax
Total Vendido = SUM(fact_ventas[importe])
```

La misma medida da `253.648.500` en una tarjeta sin filtros, `189.745.000` si el visual
está filtrado a Cócteles, y un valor distinto en cada fila de una tabla por categoría.

> **La medida no es el número. La medida es la regla para calcular el número.**

Esa es toda la diferencia. En SQL, el `WHERE` está escrito en la consulta. En DAX, el
"`WHERE`" lo pone el usuario moviendo un slicer, o el visual poniendo una categoría
en las filas. Y vos no controlás eso: controlás **cómo responde** la medida.

### Los dos contextos que hay que distinguir

| | **Contexto de fila** | **Contexto de filtro** |
|---|---|---|
| Qué es | "la fila que estoy procesando ahora" | "qué subconjunto de datos está seleccionado" |
| Dónde existe | En **columnas calculadas** y dentro de iteradores (`SUMX`, `AVERAGEX`, `FILTER`) | En **medidas**, al dibujarse |
| Se parece a | Un `for` sobre las filas | Un `WHERE` |
| Se crea con | Estar dentro de una fila | Un visual, un slicer, un filtro de página, `CALCULATE` |

**La causa del 80% de los errores de un analista que viene de SQL** es escribir una
columna calculada cuando quería una medida. La columna calculada se evalúa **una vez**,
al refrescar, y queda guardada: no responde a los filtros y ocupa memoria. La medida se
calcula en el momento y sí responde.

Regla práctica:

- ¿El valor depende de lo que el usuario filtre? → **medida**
- ¿El valor es un atributo fijo de cada fila (ej. `categoria` derivada del nombre)? → **columna calculada**
- ¿Podés calcularlo en SQL y traerlo listo? → **hacelo en SQL** (ver Parte 3)

### `CALCULATE` es el corazón de DAX

Es la función que **modifica el contexto de filtro**. Es el equivalente a agregar un
`WHERE` dentro de una medida:

```dax
Venta Cocteles = CALCULATE([Total Vendido], dim_trago[categoria] = "Cocteles")
```

Y hay una trampa que hay que entender desde el principio:

> **`CALCULATE` REEMPLAZA el filtro de esa columna, no lo suma.**

Si el usuario filtró la página a "Vinos" y vos calculás `Venta Cocteles` con
`CALCULATE(..., dim_trago[categoria] = "Cocteles")`, el resultado **no** es 0 (la
intersección de Vinos y Cócteles): es la venta de Cócteles, porque el filtro del usuario
sobre esa columna **se reemplaza**. Para que se intersecte hay que envolverlo en
`KEEPFILTERS()`.

Un `CALCULATE` con un filtro sobre una **dimensión** se comporta como un `WHERE` sobre
esa dimensión. Eso es lo que querés el 95% de las veces.

---

## Parte 2 · Los 12 patrones

Cada caso tiene tres partes: el SQL que ya sabés, el número que devuelve (verificado), y
el DAX equivalente. Los nombres de tabla siguen el modelo del
[README del proyecto](README.md): `fact_ventas`, `fact_insumos`, `dim_trago`, `dim_insumo`,
`dim_fecha`.

### 1 · Total simple

```sql
SELECT ROUND(SUM(importe), 0) FROM ventas;
```
**Devuelve:** `253.648.500`

```dax
Total Vendido = SUM(fact_ventas[importe])
```

Sin `CALCULATE`. Responde solo al filtro del visual.

### 2 · Total filtrado por una dimensión

```sql
SELECT ROUND(SUM(v.importe), 0) FROM ventas v
JOIN carta c ON c.id_trago = v.id_trago
WHERE c.categoria = 'Cocteles';
```
**Devuelve:** `189.745.000`

```dax
Venta Cocteles = CALCULATE([Total Vendido], dim_trago[categoria] = "Cocteles")
```

### 3 · `COUNT(*)` vs `COUNT(DISTINCT)` — el error más común

```sql
SELECT COUNT(*) FROM recetas;                    -- 61 filas
SELECT COUNT(DISTINCT id_insumo) FROM recetas;   -- 38 insumos distintos
```

```dax
Filas Receta      = COUNTROWS(recetas)              -- 61
Insumos en Receta = DISTINCTCOUNT(recetas[id_insumo])  -- 38
```

> **Prestá atención a este.** 61 son las *líneas* de receta; 38 son los *insumos
> distintos*. Confundirlos es el error más frecuente y no da error de sintaxis: da un
> número plausible y equivocado. En una entrevista, "¿cuál es la diferencia entre
> `COUNT(*)` y `COUNT(DISTINCT)`?" es pregunta segura.

### 4 · Promedio

```sql
SELECT ROUND(AVG(importe), 0) FROM ventas;
```
**Devuelve:** `31.942`

```dax
Ticket Promedio = AVERAGE(fact_ventas[importe])
```

> **Ojo con qué estás promediando.** `AVERAGE` promedia **filas**. En este dataset cada
> fila es una línea de venta (un trago). Si querés el ticket promedio *por pedido*,
> necesitás `DIVIDE(SUM(importe), DISTINCTCOUNT(id_pedido))`. Es la misma diferencia que
> en SQL: `AVG` promedia filas, no entidades de negocio.

### 5 · Participación sobre el total

```sql
SELECT c.categoria,
       ROUND(100.0 * SUM(v.importe) / (SELECT SUM(importe) FROM ventas), 1) AS pct
FROM ventas v JOIN carta c ON c.id_trago = v.id_trago
GROUP BY c.categoria ORDER BY pct DESC;
```

**Devuelve:** `Cocteles 74,8%` · `Cervezas 8,1%` · `Vinos 7,7%` · `Destilados 5,1%` · `Barriles 4,3%`

```dax
% del Total =
DIVIDE(
    [Total Vendido],
    CALCULATE([Total Vendido], ALL(dim_trago))
)
```

`ALL(dim_trago)` **quita el filtro** de esa dimensión, que es exactamente lo que hace la
subconsulta `(SELECT SUM(importe) FROM ventas)` en SQL.

### 6 · Acumulado (running total)

```sql
WITH s AS (SELECT semana, SUM(importe) AS t FROM ventas GROUP BY semana)
SELECT semana,
       ROUND(SUM(t) OVER (ORDER BY semana), 0) AS acumulado
FROM s ORDER BY semana;
```
**Devuelve:** la semana 1 acumula `9.254.200`; la semana 26 acumula `253.648.500` (el total).

```dax
Acumulado =
CALCULATE(
    [Total Vendido],
    FILTER(
        ALL(dim_fecha),
        dim_fecha[semana] <= MAX(dim_fecha[semana])
    )
)
```

El `OVER (ORDER BY semana)` se traduce en "traeme todas las semanas anteriores a la
actual". `ALL(dim_fecha)` es necesario para que el filtro no se aplique sobre sí mismo.

### 7 · Período anterior (`LAG`)

```sql
WITH s AS (SELECT cal.mes, SUM(v.importe) AS t
           FROM ventas v JOIN calendario cal ON cal.fecha = v.fecha
           GROUP BY cal.mes)
SELECT mes, ROUND(t, 0), ROUND(LAG(t) OVER (ORDER BY mes), 0) AS mes_previo FROM s;
```
**Devuelve:** `2024-06 → 42.493.100`, mes previo `43.253.000`

```dax
Mes Anterior =
CALCULATE([Total Vendido], DATEADD(dim_fecha[fecha], -1, MONTH))
```

> **Requisito no negociable:** `DATEADD`, `SAMEPERIODLASTYEAR` y toda la inteligencia
> temporal **exigen una tabla de fechas marcada como tabla de fechas** y con relación
> activa a la tabla de hechos. Sin eso devuelven resultados silenciosamente incorrectos.
> Se marca en: *Vista de modelo → clic derecho en la tabla → Marcar como tabla de fechas*.

### 8 · Variación porcentual período a período

```sql
-- (sobre la CTE anterior)
SELECT mes,
       ROUND(100.0 * (t - LAG(t) OVER (ORDER BY mes))
             / LAG(t) OVER (ORDER BY mes), 1) AS var_pct FROM s;
```
**Devuelve:** `2024-02 −1,4%` · `2024-03 +15,4%` · `2024-04 −13,4%` · `2024-05 +7,5%` · `2024-06 −1,8%`

```dax
Var % vs Mes Anterior =
DIVIDE([Total Vendido] - [Mes Anterior], [Mes Anterior])
```

> **Usá siempre `DIVIDE`, no el operador `/`.** `DIVIDE` devuelve vacío en vez de error
> cuando el denominador es 0. El operador `/` **rompe la medida** con un error que se
> propaga por todo el tablero. Es la causa #1 de tableros que muestran "Error" en blanco.

### 9 · Ranking

```sql
SELECT id_trago, ROUND(SUM(importe), 0) AS t,
       RANK() OVER (ORDER BY SUM(importe) DESC) AS posicion
FROM ventas GROUP BY id_trago ORDER BY posicion LIMIT 5;
```
**Devuelve:** `Gin Tonic 21.592.800 (1)` · `Fernet con Cola 20.345.600 (2)` · `Mojito 16.543.000 (3)`

```dax
Ranking Trago = RANKX(ALL(dim_trago), [Total Vendido])
```

`RANKX` ordena descendente por defecto, igual que `RANK() OVER (... DESC)`.

### 10 · Top N dentro de cada grupo (`PARTITION BY`)

```sql
WITH r AS (
  SELECT categoria, nombre_insumo, costo_actual,
         ROW_NUMBER() OVER (PARTITION BY categoria
                            ORDER BY costo_actual DESC) AS rn
  FROM insumos)
SELECT categoria, nombre_insumo, ROUND(costo_actual, 0)
FROM r WHERE rn <= 2 ORDER BY categoria;
```
**Devuelve:** `Amargos → Angostura 8.900, Bitter de chocolate 8.200` · `Barriles → Barril IPA 96.000, Barril Lager 78.000` · …

```dax
-- NO existe un equivalente limpio como medida.
-- Se resuelve en el VISUAL: usar un gráfico y aplicar
-- Filtros → "N superior" → Mostrar elementos: 2 → Por valor: [Costo Total]
```

> **Lección importante:** no todo se traduce 1 a 1 de SQL a DAX. `PARTITION BY` es el caso
> típico: en DAX se resuelve con una funcionalidad del visual, no con una fórmula. Cuando
> algo no se traduce, la respuesta no es "forzar la fórmula": es **elegir la herramienta**.

### 11 · Cantidad de filas

```sql
SELECT COUNT(*) FROM ventas;   -- 7.941
```

```dax
Cantidad de Ventas = COUNTROWS(fact_ventas)
```

### 12 · Condicional (`CASE WHEN`)

```sql
SELECT ROUND(SUM(CASE WHEN cal.dia_semana IN ('Sabado','Domingo')
                      THEN v.importe ELSE 0 END), 0) AS fin_de_semana,
       ROUND(SUM(CASE WHEN cal.dia_semana NOT IN ('Sabado','Domingo')
                      THEN v.importe ELSE 0 END), 0) AS entre_semana
FROM ventas v JOIN calendario cal ON cal.fecha = v.fecha;
```
**Devuelve:** fin de semana `98.963.800` · entre semana `154.684.700`

```dax
Venta Fin de Semana =
CALCULATE([Total Vendido], dim_fecha[dia_semana] IN {"Sabado", "Domingo"})
```

Fijate que el SQL devuelve **dos columnas** en una sola consulta; en DAX son **dos
medidas**. Es el patrón general: en DAX cada número que mostrás es una medida propia.

---

## Parte 3 · La regla de arquitectura que casi todos ignoran

**La lógica pesada va en SQL. Power BI hace agregaciones e interacción.**

El reporte de variación del bar necesita: multiplicar ventas por recetas, sumar por
insumo y semana, restar el uso teórico del real, multiplicar por el costo por mililitro.
Eso **no se hace en DAX**. Se hace en SQL, se guarda como una vista o tabla
(`mart_variacion`), y Power BI la importa como una tabla de hechos común.

Por qué:

| | En SQL (el *marts*) | En DAX |
|---|---|---|
| Se versiona y se revisa | ✅ es código | ❌ vive en un `.pbix` binario |
| Se testea | ✅ con un `SELECT` | ❌ a ojo |
| Se reusa | ✅ cualquier herramienta | ❌ solo Power BI |
| Velocidad | ✅ se calcula una vez | ❌ se recalcula en cada interacción |

**Regla práctica:** en DAX debería quedar solo lo que **depende del filtro del usuario**
(participaciones, acumulados, comparaciones contra el período anterior). Todo lo demás,
en SQL.

Eso además te da una ventaja concreta en una entrevista: cuando te pregunten "¿por qué no
lo hiciste en DAX?", tenés una respuesta de arquitectura, no una excusa.

---

## Parte 4 · Los 6 errores clásicos

| # | Error | Por qué pasa | Cómo se evita |
|---|---|---|---|
| 1 | Columna calculada donde iba una medida | Viene de pensar en SQL (`SELECT ... AS`) | Si depende del filtro del usuario, es medida |
| 2 | `CALCULATE` que "no filtra" | `CALCULATE` **reemplaza** el filtro de la columna | Envolver en `KEEPFILTERS()` si querés intersectar |
| 3 | Inteligencia temporal que da basura | Falta marcar la tabla de fechas | Marcar como tabla de fechas + relación activa |
| 4 | `/` en vez de `DIVIDE` | Es lo natural viniendo de SQL | `DIVIDE()` siempre que el denominador pueda ser 0 |
| 5 | `FILTER` sobre la tabla de hechos | Parece más directo | Filtrar **dimensiones**; sobre hechos es lento |
| 6 | Relaciones bidireccionales "para que funcione" | Tapa un problema de modelado | Modelo estrella bien armado, relaciones 1:* en un sentido |

---

## Parte 5 · Cómo verificar TU DAX (10 minutos, y es tu responsabilidad)

No puedo ejecutar DAX desde acá. Pero sí te dejé el método: **cada medida tiene un número
SQL verificado contra el que compararla.**

1. Cargá el modelo en Power BI Desktop.
2. Insertá un **visual de tarjeta** (Card) y poné la medida, **sin ningún filtro** en la página.
3. Compará contra el número de esta guía:

| Medida | Debe dar |
|---|---|
| `Total Vendido` | **253.648.500** |
| `Venta Cocteles` | **189.745.000** |
| `Cantidad de Ventas` | **7.941** |
| `Ticket Promedio` | **31.942** |
| `Venta Fin de Semana` | **98.963.800** |
| `Filas Receta` | **61** |
| `Insumos en Receta` | **38** |

4. Si coinciden, tus medidas están bien. **Si alguna no coincide, la medida está mal,
no los datos** — y ya sabés exactamente cuál es el número correcto.
5. Para las medidas que dependen del tiempo (`Mes Anterior`, `Acumulado`, `Var %`),
   poné `dim_fecha[mes]` en el eje de una tabla y compará con la Parte 2 de esta guía.

> **Esto es lo que hace un analista que trabaja bien:** antes de mostrar un número,
> lo valida contra una fuente independiente. No "me parece que está bien": lo compara.

---

## Resumen: la tabla de traducción

| SQL | DAX |
|---|---|
| `SUM(col)` | `SUM(tabla[col])` |
| `AVG(col)` | `AVERAGE(tabla[col])` |
| `COUNT(*)` | `COUNTROWS(tabla)` |
| `COUNT(DISTINCT col)` | `DISTINCTCOUNT(tabla[col])` |
| `WHERE dim.col = "x"` | `CALCULATE([Medida], dim[col] = "x")` |
| `WHERE dim.col IN (...)` | `CALCULATE([Medida], dim[col] IN {...})` |
| `SUM(x) / (SELECT SUM(x) ...)` | `DIVIDE([M], CALCULATE([M], ALL(dim)))` |
| `SUM() OVER (ORDER BY ...)` | `CALCULATE([M], FILTER(ALL(dim_fecha), ... <= MAX(...)))` |
| `LAG(x) OVER (ORDER BY ...)` | `CALCULATE([M], DATEADD(dim_fecha[fecha], -1, MONTH))` |
| `RANK() OVER (ORDER BY x DESC)` | `RANKX(ALL(dim), [M])` |
| `ROW_NUMBER() OVER (PARTITION BY ...)` | No hay medida equivalente: se hace con el filtro "N superior" del visual |
| `SUM(CASE WHEN c THEN x END)` | `CALCULATE([M], filtro)` |
| `GROUP BY` | Dimensiones en filas del visual, no una medida |
