# Proyecto 3 — Tablero de control de un bar · Power BI

**Tesis:** *"El tablero que le dice al dueño cuánta plata se le está perdiendo, dónde, y qué hacer al respecto."*

**Semanas:** 8–10

> **Por qué el bar y no el retail.** Este proyecto podría ser un dashboard genérico de
> ventas del dataset de retail. Sería correcto y olvidable. El tablero del bar tiene algo
> que ningún template de Power BI tiene: **mide pérdida, no venta.** Muestra cuánta plata
> se perdió, en qué insumo, en qué semana, y qué causa lo explica. Eso es control de
> gestión, y es lo que diferencia un portafolio de un ejercicio.

---

## De dónde salen los datos

De [`datos/bar/`](../../datos/bar/) — el mismo dataset del Proyecto 4, con **5 causas de
merma inyectadas** y verificadas. Se puede construir y validar el tablero completo **antes**
de tener los datos reales del bar.

> **Nota sobre la limpieza:** este dataset **no tiene defectos estructurales** (no hay
> claves huérfanas, duplicados ni tipos rotos). La suciedad acá es *operativa*: falta un
> remito, un comp no se registró, un conteo se hizo mal. Es el contraste con el Proyecto 2,
> donde sí había que limpiar antes de modelar. Acá se modela directo.
>
> Regenerar la base: `python scripts/generar_dataset_bar.py`

### Qué se calcula en SQL y qué en DAX

**Regla de arquitectura: la lógica pesada en SQL, la interacción en Power BI.**
El detalle y el porqué están en [`01_sql_a_dax.md`](01_sql_a_dax.md#parte-3--la-regla-de-arquitectura-que-casi-todos-ignoran).

**Vistas `mart_` que hay que construir en SQL** (esto es trabajo de este proyecto, y es
código versionado que se puede testear):

| Vista | Grano | Qué contiene |
|---|---|---|
| `mart_variacion` | insumo × semana | uso_real_ml, uso_teorico_ml, variacion_ml, variacion_pesos |
| `mart_costo_trago` | trago | costo de insumos, precio de venta, margen de contribución |
| `mart_ventas_trago` | trago × mes | unidades, facturación, margen total |

El SQL del reporte de variación ya está escrito y verificado en
`datos/bar/BAR_CLAVE_NO_ABRIR.md` (spoiler local) — usalo como punto de partida, no como
caja negra: **tenés que poder explicarlo línea por línea.**

---

## Modelo estrella

```
        dim_fecha                    dim_insumo
       (calendario +               (insumos +
        anio, mes_numero,           categoria,
        nombre_mes, es_finde)       costo por unidad)
            │                            │
            └──────► fact_variacion ◄────┘
                     (insumo × semana)
                     uso_real_ml
                     uso_teorico_ml
                     variacion_ml
                     variacion_pesos

        dim_fecha      dim_trago        dim_turno
            │              │                │
            └──────► fact_ventas ◄─────────┘
                     (línea de venta)
                     cantidad, precio, importe
```

**Checklist del modelo:**

- [ ] Una sola tabla de hechos por proceso (ventas y variación son dos procesos distintos: está bien tener dos)
- [ ] `dim_fecha` creada con DAX o en SQL, con **columna de fecha continua** y **marcada como tabla de fechas**
- [ ] Relaciones 1 a muchos, dirección **única** desde la dimensión hacia el hecho
- [ ] Ninguna relación bidireccional sin justificar por escrito
- [ ] Medidas agrupadas en una tabla `_Medidas` (no sueltas por el modelo)
- [ ] Dimensiones sin columnas que no se usen
- [ ] Nombres legibles: `Total Vendido`, no `Sum of importe`

---

## Las 3 páginas

**Regla de diseño:** cada página responde **una** pregunta, y el título **afirma**, no nombra.
"Las ventas caen por la categoría X" es un título. "Ventas por categoría" es una etiqueta.

### Página 1 · Control de merma *(la más importante)*

Pregunta: **¿cuánta plata se está perdiendo, en qué insumo y en qué semana?**

- Tarjetas: merma total en pesos y como % de las ventas
- Barras horizontales: **top 10 insumos por variación en pesos** ← ordenado por plata, no por ml
- Línea: variación semanal total (para ver tendencias, no solo el acumulado)
- Matriz: insumo × semana, con formato condicional, para ubicar el pico

**Detalle que hay que mostrar sí o sí:** un visual que compare el ranking **por mililitros**
contra el ranking **por pesos**. Es el hallazgo del proyecto y hay que hacerlo visible, no
solo contarlo en el README.

### Página 2 · Rentabilidad de la carta (ingeniería de menú)

Pregunta: **¿qué tragos sostienen el negocio y cuáles hay que sacar de la carta?**

- **Scatter plot:** popularidad (unidades) en X, margen de contribución en Y
- Líneas de referencia en el promedio de cada eje → los 4 cuadrantes de Kasavana & Smith
- Colores por cuadrante: Estrellas / Caballos de tiro / Enigmas / Perros
- Tabla con la acción recomendada por cuadrante

Los umbrales y qué hacer con cada cuadrante están en
[`../04_estrella/01_catalogo_analisis.md`](../04_estrella/01_catalogo_analisis.md) (análisis A3).

### Página 3 · Operación

Pregunta: **¿cuándo trabaja el bar y con qué mix?**

- Barras por día de la semana y por turno
- Evolución mensual de la facturación
- Mix por categoría de trago

---

## Medidas DAX a construir

La traducción desde SQL, con el número que tiene que dar cada una, está en
[`01_sql_a_dax.md`](01_sql_a_dax.md). Mínimo:

| Medida | Verificada contra |
|---|---|
| `Total Vendido` | 253.648.500 |
| `Cantidad de Ventas` | 7.941 |
| `Venta Cocteles` | 189.745.000 |
| `Ticket Promedio` | 31.942 |
| `Venta Fin de Semana` | 98.963.800 |
| `Merma Total $` | (ver clave local) |
| `Merma % de Ventas` | (ver clave local) |
| `Mes Anterior` / `Var % vs Mes Anterior` | serie mensual |
| `Acumulado` | semana 26 = total |
| `% del Total` por categoría | Cocteles 74,8% |
| `Ranking Insumo` por merma | top por pesos |
| `Margen por Trago` | `mart_costo_trago` |
| `Segmento Carta` (Estrella/Perro/…) | promedio ponderado de cada eje |

- [ ] Todas las medidas **validadas contra el número SQL** antes de mostrarlas
- [ ] Cada medida con una descripción en el modelo (para que otro la entienda)
- [ ] `DIVIDE` en vez de `/` en toda división

---

## Entregables

| Archivo | Qué es |
|---|---|
| `tablero_bar.pbix` | El archivo de Power BI |
| `sql/marts.sql` | Las vistas `mart_` versionadas |
| `docs/modelo.png` | Diagrama del modelo estrella |
| `docs/diccionario_medidas.md` | Cada medida: qué responde, fórmula, y el número de validación |
| `docs/decisiones.md` | Qué calculaste en SQL, qué en DAX, y por qué |
| `docs/narrativa.pdf` | 2 páginas: situación → hallazgo → acción |

## Hallazgos
1.
2.
3.

## Recomendaciones
1.
2.

## Limitaciones
-

## Prueba de defensa
- [ ] Explico la diferencia entre medida y columna calculada con un ejemplo mío
- [ ] Explico qué hace `CALCULATE` y qué significa que "reemplaza" el filtro
- [ ] Justifico qué dejé en SQL y qué en DAX, con argumento de arquitectura
- [ ] Muestro cómo validé cada medida contra un número independiente
- [ ] Puedo explicar por qué el ranking por mililitros engaña y el de pesos no
