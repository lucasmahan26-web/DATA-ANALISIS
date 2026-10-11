# Los 8 análisis que se pueden hacer con el inventario de un bar

> Esto no es relleno teórico: son los análisis que la industria de bares **paga** por tener
> y que la mayoría de los bares **nunca corre**. Leelos y vas a entender por qué tu caso es
> una ventaja y no una anécdota simpática.

---

## A0. Por qué el inventario de un bar es un dataset excepcional

Un bar tiene una propiedad que casi ningún otro negocio tiene: **podés calcular cuánto
deberías haber consumido y compararlo con lo que realmente consumiste.**

Eso se llama **reporte de variación**, y es la diferencia entre "sé cuánto vendí" y "sé cuánto
se me perdió y por qué".

Casi ningún analista de datos junior tiene acceso a eso. Vos sí, porque trabajás ahí. Una
empresa de software o un e-commerce no puede hacer este análisis: no tienen un inventario
físico que contar dos veces.

**En una entrevista, decir *"hice un reporte de variación de inventario de un bar real"* te
pone en otra categoría.** Es un análisis de control de gestión, no un ejercicio de curso.

---

## A1. El reporte de variación — tu análisis estrella

Es el análisis más valioso y el más difícil de replicar. Calcula **qué se perdió**, no solo
qué se vendió.

### Las dos fórmulas

```
Uso real   = (conteo anterior + entregas) − conteo actual
Variación  = uso real − ventas registradas en el POS
```

### Cómo se calcula "cuánto deberías haber usado"

Para eso necesitás las **recetas**. Si un Negroni lleva 30 ml de gin, y vendiste 40 Negronis,
deberías haber consumido 1.200 ml de gin. Eso es el *uso teórico*.

```
Variación = uso real − uso teórico
```

**Unidad de medida obligatoria: mililitros, no botellas.** Las botellas vienen de distintos
tamaños (700 ml, 750 ml, 1 L), así que contar en botellas mezcla unidades y arruina el cálculo.

### Los benchmarks de la industria

| Variación sobre el inventario | Diagnóstico |
|---|---|
| Menos de 1% | Excelente |
| 1% a 2% | Sano — el objetivo de trabajo |
| 2% a 4% | Necesita revisión |
| Más de 5% | Investigar ya |

Muchos bares operan entre 5% y 25% **sin saberlo**, porque nunca corren este reporte.

### Las 4 causas, EN ORDEN de frecuencia

Esto es lo que separa un análisis amateur de uno profesional. El orden importa muchísimo:

1. **Error de conteo** — la causa más común. Ante un pico raro, **recontá antes de concluir
   cualquier cosa**. Este es el error que comete todo el mundo: saltar a la conclusión grave.
2. **Over-pouring y derrames** — la causa operativa de más volumen. Un bartender que sirve
   libremente 60 ml donde la receta dice 45 ml regala una botella cada 30 tragos.
3. **Problemas de papel** — un remito que nunca se cargó, una receta mal mapeada en el POS,
   una transferencia a la cocina que nadie registró.
4. **Producto no registrado** — comps que se sirvieron pero no se cobraron, tragos del
   personal, robo. **Es el bucket al que todos saltan primero**, y por eso hay que revisar
   los otros tres antes.

### La dirección de la variación también informa

- **Variación negativa** (falta producto respecto de las ventas) → es la dirección de la pérdida.
- **Variación positiva** (las ventas superan el uso) → **no es una buena noticia, es un número
  roto.** Casi siempre es un error de registro: falta una factura, o hubo un mal conteo.

### Cómo pasar de "un pico" a "un patrón"

Un pico aislado suele ser un error de conteo. **El mismo producto desviado tres semanas
seguidas es un problema de proceso.** Ahí está el análisis de verdad: buscá patrones, no
incidentes.

### La matemática que convence a un dueño

Es el argumento que tenés que poder decir de memoria:

> Un bar con $60.000 de ventas mensuales de bebida y 22% de pour cost usa ~$13.200 en
> producto. Una variación del 4% son **$528 de producto por mes sin explicación**. Ese
> producto, vendido al mismo pour cost, debería haber generado **$2.400 de ingreso**.
> En un año: **~$29.000 recuperables con un conteo semanal.**

Ese párrafo, con los números de *tu* bar, es tu proyecto.

---

## A2. Pour cost (costo de vertido)

El indicador clásico de la industria. Mide qué porcentaje de tu ingreso por bebida se lo come
el costo del producto.

```
Pour cost = (inventario inicial + compras − inventario final) / ventas de bebida × 100
```

### Benchmarks por categoría

| Categoría | Rango objetivo |
|---|---|
| Destilados | 18–25% |
| Cócteles | 20–25% |
| Cerveza de barril | 15–18% |
| Cerveza envasada | 20–26% |
| Vino por copa | 28–35% |
| **Mezcla total (blended)** | **20–28%** |

**El vino por copa es más caro y está bien que lo sea.** Una botella rinde 4-5 copas y lo que
sobra se oxida: es desperdicio estructural de la categoría, no un fallo de control.

### Y acá está la trampa que casi nadie ve

**Tu pour cost puede verse inflado aunque sirvas perfecto.** Si los comps, las invitaciones y
las bebidas sin cobrar no se registran en el POS, tu denominador (ventas de bebida) queda
**más chico de lo real**, y un denominador más chico da un porcentaje más alto.

> **Arreglá los datos antes de culpar a los bartenders.** Si el número de ventas está mal,
> ninguna capacitación de jigger va a bajar el porcentaje.

Ese hallazgo — "el problema no era el servicio, era el registro"— es exactamente el tipo de
conclusión que un gerente valora, y que solo se ve mirando los datos con criterio.

### Y el dato que cambia la conversación con el dueño

**El mix de ventas determina tu pour cost mezclado más que el precio de cada trago.** Un bar
que saca 60% de su ingreso de barril y vino corre un 26-28% estructural; el mismo menú con 60%
de cócteles de la casa baja a 22-24% **sin cambiar un solo precio**. Es la palanca que casi
nadie usa porque todos miran el precio individual.

---

## A3. Ingeniería de menú (Kasavana & Smith)

Este es el análisis más "consultor" y **el que mejor se ve en un tablero de Power BI**.

Es un marco clásico de la industria (Michael Kasavana y Donald Smith, 1982): clasificás cada
trago cruzando **popularidad** con **rentabilidad**.

### Los ejes

- **Popularidad:** unidades vendidas. El criterio estándar es comparar contra el **70% del
  promedio** de ventas de la categoría.
- **Rentabilidad:** margen de contribución (precio de venta − costo de los insumos), comparado
  contra el margen promedio ponderado.

### La matriz y qué hacer con cada cuadrante

| | **Alta rentabilidad** | **Baja rentabilidad** |
|---|---|---|
| **Alta popularidad** | ⭐ **Estrellas**<br>Mantener, destacar en la carta, no tocar el precio | 🐴 **Caballos de tiro**<br>Subir precio con cuidado o bajar el costo de la receta |
| **Baja popularidad** | 🧩 **Enigmas**<br>Promocionar, reubicar en la carta, sugerir desde el servicio | 🐕 **Perros**<br>Eliminar de la carta |

**Por qué esto impresiona:** no es un gráfico de barras. Es un **scatter plot con umbrales y
una recomendación de acción por cuadrante**. Demuestra que sabés convertir un análisis en una
decisión, que es literalmente la definición del trabajo de un analista.

---

## A4. Análisis ABC (Pareto) del inventario

Ordenás los insumos por valor de consumo anual y acumulás el porcentaje.

- **A (primer ~80% del valor):** pocos insumos, control estricto, conteo semanal.
- **B:** control medio.
- **C (el resto):** muchos insumos, poco valor, control trimestral.

**Para qué sirve:** no podés contar 200 insumos con el mismo rigor. Con ABC sabés **dónde poner
el esfuerzo** — y eso es criterio de gestión, no una tabla.

---

## A5. Rotación de inventario y capital inmovilizado

```
Rotación = consumo del período / inventario promedio
```

Un insumo de baja rotación es **plata parada en la estantería** más riesgo de vencimiento o
deterioro. Los candidatos típicos en un bar: licores de nicho que se usaron una vez para un
trago que ya no está en la carta.

---

## A6. Quiebres de stock (los "86")

Productos que se agotaron. El análisis es de **costo de oportunidad**: cada vez que un cliente
pide un trago y no lo tenés, perdés esa venta **y** la posibilidad de vender algo más caro en
su lugar.

Con ventas por producto podés estimar cuántas unidades se habrían vendido, usando el promedio
de los días en que sí había stock. Es una estimación, y decirlo así es parte de la honestidad
del análisis.

---

## A7. Patrones temporales

Ventas por **día de la semana**, por **turno** y por **mes**.

- Sirve para **dotación de personal**: ¿el martes necesitás tres personas o dos?
- Sirve para **compras**: no compres perecederos igual todas las semanas.
- Y da la estacionalidad, que es el contexto de todo lo demás.

---

## A8. Deriva de precios de compra

El mismo insumo comprado a precios distintos a lo largo del tiempo.

**Por qué es crítico acá:** con inflación, el pour cost calculado con precios viejos **miente**.
El análisis honesto usa el precio de la última factura, no el del catálogo.

Y hay un hallazgo típico: **el mismo producto comprado a dos proveedores distintos a precios
distintos.** Recuperar 1 punto de pour cost moviendo el mix de proveedores puede valer más que
cualquier campaña de ventas.

---

## La matemática del over-pouring (tenela lista)

Es el argumento que más impacta a un dueño, porque es chico y concreto:

> Un bartender que sirve 60 ml donde la receta dice 45 ml regala el 33% de cada botella.
> Con 200 tragos por semana, esos 15 ml extra por trago **equivalen a una botella perdida
> cada 30 tragos**.

Podés calcularlo con *tus* números y ponerlo en el README. Va a ser el párrafo que más te
pregunten en la entrevista.

---

## El modelo de datos ideal

No vas a tener todo esto. El [diagnóstico](02_diagnostico_y_privacidad.md) te dice qué tenés
y qué se puede hacer con eso. Pero este es el objetivo:

```
insumos(id_insumo, nombre, categoria, unidad_base, contenido_por_envase, es_reventa_directa)

recetas(id_trago, id_insumo, cantidad)              -- la receta estandarizada
carta(id_trago, nombre, precio_venta, categoria)    -- precio y categoría de cada trago

ventas(fecha, turno, id_trago, cantidad, precio)    -- del POS
conteos(fecha, id_insumo, cantidad_contada)         -- los conteos físicos
compras(fecha, id_insumo, cantidad, precio_unitario, id_proveedor)
```

Con eso podés calcular **los 8 análisis** de este documento. Sin recetas podés hacer 6 de 8:
te faltan variación y costo por trago.

---

## Fuentes

- Pour cost: fórmulas, benchmarks por categoría y el problema del dato sucio —
  [Otter — Liquor Cost Percentage](https://www.tryotter.com/blog/restaurant-tips/liquor-cost-percentage)
- Reporte de variación: fórmula, benchmarks y los 4 buckets de causas —
  [Drinks By Neat — The Variance Report](https://drinksbyneat.com/blog/variance-report/)
- Ingeniería de menú (Kasavana & Smith) —
  [Artículo académico sobre la matriz de Kasavana-Smith](https://www.ajhtl.com/uploads/7/1/6/3/7163688/article_4_14_5_989-998.pdf)
- Control de costos de bebida —
  [MarketMan — Beverage Cost Control Systems](https://www.marketman.com/blog/beverage-cost-control-systems)
