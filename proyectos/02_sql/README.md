# Proyecto 2 — SQL End-to-End (PostgreSQL)

**Tesis:** *"10 preguntas de negocio respondidas sobre una base relacional, con SQL reproducible y documentado."*

**Semanas:** 5–7

---

## Problema de negocio
<!-- TODO -->

## Datos y fuentes
| Campo | Valor |
|---|---|
| Dataset | Modelo relacional de 7 tablas de la misma cadena de supermercados del Proyecto 1 |
| Origen | Generado con [`scripts/generar_dataset_p2.py`](../../scripts/generar_dataset_p2.py), semilla fija → reproducible |
| Tablas | 7 (6 dimensiones + 1 de hechos) |
| Filas totales | **131.122** (130.688 líneas de venta en 45.000 pedidos) |
| Periodo | 2023-01-01 a 2024-12-31 |
| Licencia | Sintético, uso libre |
| Base de datos | `analisis` (PostgreSQL local) |
| Scripts | [`P2_01_crear_tablas.sql`](../../scripts/P2_01_crear_tablas.sql), [`P2_02_agregar_constraints.sql`](../../scripts/P2_02_agregar_constraints.sql) |

**Modelo:**

```
categorias ──< productos ──< ventas >── sucursales
                                │
                                ├── vendedores >── sucursales
                                ├── clientes
                                └── medios_pago
```

`ventas` es la tabla de hechos. `id_pedido` es una clave degenerada: **un pedido tiene
varias líneas**, así que el ticket promedio se calcula agrupando por `id_pedido`, no por
`id_venta`. Ese detalle es el 80% de los errores en las pruebas técnicas.

> ⚠️ **No abras el archivo `datos/p2/P2_CLAVE_NO_ABRIR.md` hasta terminar.**
> Contiene los 15 defectos, sus conteos y las consultas de verificación.
> Es tu autoevaluación local y **no se publica** en el repositorio.

## Checklist de calidad de datos (esto SÍ lo tenés que resolver vos)

El dataset tiene **15 problemas** inyectados. Sabés *qué familias* buscar; el *cómo*
es el ejercicio. Documentá el conteo que encontrás para cada uno antes de mirar la clave.

**Sobre la tabla de hechos `ventas`:**
- [ ] Claves primarias duplicadas
- [ ] Claves foráneas huérfanas — hay **5** columnas afectadas (encontrá cuáles)
- [ ] Nulos en una clave foránea
- [ ] Fechas fuera del periodo del negocio
- [ ] Cantidades cero
- [ ] Cantidades negativas (¿devoluciones?)
- [ ] Precios no positivos
- [ ] Descuentos fuera del rango 0–1
- [ ] Importes que no cuadran con `cantidad × precio × (1 − descuento)`

**Sobre las dimensiones:**
- [ ] Una dimensión con clave primaria duplicada
- [ ] Una dimensión que apunta a una categoría inexistente
- [ ] Una dimensión que apunta a una sucursal inexistente

> **El orden importa.** No podés crear las PK/FK antes de limpiar: el motor va a
> rechazar la carga. Ver el orden de trabajo completo en el script
> [`P2_02_agregar_constraints.sql`](../../scripts/P2_02_agregar_constraints.sql).

> ✅ **Los dos scripts SQL están verificados contra PostgreSQL 18 de verdad.**
> El DDL ejecuta sin errores, los 7 CSV cargan con `\copy` con los conteos exactos,
> y las constraints **efectivamente rechazan** los datos crudos. Podés comprobarlo vos
> mismo con `scripts/verificar_postgres.ps1`, que levanta un clúster temporal en el
> puerto 5433 (sin tocar tu base) y hace toda la prueba.
>
> Ya tenés **PostgreSQL 18.4 instalado y el servicio corriendo**, así que este proyecto
> usa el motor real desde el primer día, no el SQLite de práctica.

## Mapa de trabajo

- [ ] Crear las tablas sin constraints
- [ ] Cargar los 7 CSV
- [ ] Diagnosticar los 15 defectos y **anotar tus conteos en un archivo antes de mirar la clave**
- [ ] Limpiar y documentar cada decisión
- [ ] Agregar PK y FK (si falla, todavía hay basura)
- [ ] Construir las vistas de negocio siguiendo la
      [**especificación de la capa `marts`**](01_marts.md) ← las 4 vistas, con grano y columnas
- [ ] Responder las 10 preguntas **sobre los marts**, sin `JOIN` a las tablas crudas
- [ ] Escribir el diccionario de datos

> **Por qué existe la capa `marts`:** sin ella tenés 10 definiciones distintas de "venta neta",
> una por consulta, y a los dos meses nadie sabe por qué dos reportes dan números distintos.
> Los marts definen cada métrica **una sola vez**. El detalle y las 5 decisiones de negocio que
> tenés que tomar están en [`01_marts.md`](01_marts.md).

## Estructura del repositorio
```
proyectos/02_sql/
├── README.md
├── sql/
│   ├── 01_staging.sql   # carga a tablas de trabajo + limpieza (lo escribís vos)
│   ├── 02_marts.sql     # vistas de negocio: CTEs, window functions
│   └── 03_analisis.sql  # las 10 preguntas
├── docs/
│   ├── diccionario_datos.md
│   ├── conteos_diagnostico.md   # TUS conteos, antes de mirar la clave
│   └── modelo.png               # diagrama de relaciones
└── hallazgos.md

scripts/P2_01_crear_tablas.sql         # DDL sin constraints (dado)
scripts/P2_02_agregar_constraints.sql  # PK y FK, al final (dado)
datos/p2/*.csv                         # las 7 tablas en crudo (dado)
```

## Modelo de datos
_(Diagrama de tablas y relaciones. Pegar imagen o link.)_
<!-- TODO -->

## Las 10 preguntas de negocio
_(Fórmulas del tema, no "¿cuántas filas hay?". Cada una debe terminar en una decisión.)_

| # | Pregunta de negocio | Técnica SQL usada | Respuesta | Implicancia |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

## Conceptos SQL que este proyecto debe demostrar
- [ ] `JOIN` (INNER, LEFT) y `LEFT JOIN ... IS NULL` para encontrar faltantes
- [ ] `GROUP BY` + `HAVING`
- [ ] Subconsultas y `EXISTS`
- [ ] CTEs (`WITH`) encadenadas
- [ ] `CASE WHEN` para segmentar
- [ ] Funciones de ventana: `ROW_NUMBER()`, `RANK()`, `LAG()/LEAD()`, `SUM() OVER (...)`
- [ ] Funciones de fecha (`DATE_TRUNC`, intervalos)
- [ ] `COALESCE` y manejo de nulos
- [ ] Chequeos de calidad de datos (duplicados, huérfanos, rangos inválidos)

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
- [ ] Escribo un JOIN + GROUP BY + window function sin mirar sintaxis
- [ ] Sé explicar por qué usé CTE en vez de subconsulta
- [ ] Puedo hablar de performance (índices, evitar `SELECT *`, filtrar antes de agregar)
