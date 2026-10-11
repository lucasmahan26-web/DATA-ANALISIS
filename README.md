<!--
  ============================================================================
  README DEL PORTAFOLIO
  ============================================================================
  Este es el archivo que un reclutador lee primero. Es tu vidriera.
  Objetivo: que en 30 segundos entienda qué sabés hacer y vea evidencia.

  Los [CORCHETES] son para completar. Los bloques <!-- COMPLETAR --> marcan
  lo que falta. Cuando termines cada proyecto, reemplazá el placeholder por
  el resultado real.

  NO escribas nada que no puedas defender en una entrevista.
  ============================================================================
-->

# [Tu Nombre Completo] — Analista de Datos

[Tu Ciudad] · [tu@email.com] · [LinkedIn](https://linkedin.com/in/tu-perfil)

Profesional de **[tu área actual]** orientándome a análisis de datos. Trabajo con
**Excel avanzado (Power Query), SQL y Power BI** para convertir datos desordenados en
información que se usa para decidir. Aporto conocimiento del negocio de **[tu rubro]**
y nivel de inglés intermedio-avanzado.

---

## Stack

| | |
|---|---|
| **Excel** | Power Query, Power Pivot, DAX básico, tablas dinámicas, tablas de búsqueda |
| **SQL** | PostgreSQL, SQLite — JOIN, CTE, funciones de ventana, subconsultas, calidad de datos |
| **BI** | Power BI — modelo estrella, medidas DAX, storytelling con datos |
| **Python** | pandas, numpy, matplotlib, Jupyter |
| **Otros** | Git, GitHub, modelado de datos, documentación de procesos |

---

## Proyectos

> Cada proyecto está documentado con la misma estructura:
> **problema de negocio → datos → proceso y decisiones → hallazgos → recomendaciones → limitaciones.**
> Las decisiones de limpieza y los criterios de negocio están escritos a propósito:
> un número sin criterio documentado no sirve dentro de seis meses.

### 1. Automatización de un reporte de ventas · Excel + Power Query

Un reporte mensual de ventas que se armaba a mano —copiando y pegando de tres
exportaciones distintas— tardaba **6 horas por mes**. El problema no era solo el tiempo:
cuando el reporte estaba listo, la información ya tenía una semana y nadie confiaba
del todo en los números.

Reconstruí el proceso completo en Power Query sobre la exportación cruda del sistema
(**2.935 filas × 14 columnas, todo como texto**), con **12 tipos de problemas de calidad
de datos** resueltos y documentados paso a paso.

**Resultado:** [COMPLETAR — ej: el reporte pasó de 6 horas a 10 minutos por mes, y X% de las filas tenían algún error que hoy está controlado]

**Decisiones que vale la pena mirar:** [COMPLETAR — ej: por qué separé las devoluciones en una consulta aparte en vez de filtrarlas]

[Ver el proyecto →](proyectos/01_excel_powerquery/)

---

### 2. Modelado y calidad de datos · SQL / PostgreSQL

<!-- COMPLETAR cuando termines P2 -->

Modelé una base relacional de **7 tablas y 131.122 registros** (líneas de venta,
productos, sucursales, vendedores, clientes, medios de pago y calendario), diagnostiqué
**15 tipos de problemas de integridad** y documenté cada corrección. Cerré el trabajo
agregando las claves primarias y foráneas: el motor rechaza la carga hasta que los datos
son consistentes, así que las restricciones son la prueba objetiva de que la limpieza
está completa.

**Resultado:** [COMPLETAR]

**Lo más interesante:** [COMPLETAR — ej: qué hice con las cantidades negativas y por qué]

[Ver el proyecto →](proyectos/02_sql/)

---

### 3. Tablero de control de bar · Power BI

<!-- COMPLETAR cuando termines P3 -->

Un tablero que no mide ventas, mide **pérdida**: cuánta plata se pierde, en qué insumo, en
qué semana, y qué causa lo explica. Modelo estrella con dos tablas de hechos (ventas y
variación de inventario), tabla de fechas marcada y las medidas DAX validadas una por una
contra los números del SQL equivalente.

Incluye la matriz de **ingeniería de menú de Kasavana & Smith** (popularidad × rentabilidad
→ Estrellas / Caballos de tiro / Enigmas / Perros) y un visual que contrasta el ranking de
merma **por mililitros** contra el ranking **por pesos** — la diferencia que hace visible
por qué el volumen esconde las pérdidas.

**Resultado:** [COMPLETAR]

**Decisión de arquitectura:** la lógica pesada (multiplicar ventas por recetas, calcular
variación) vive en vistas SQL versionadas y testeables; en DAX quedó solo lo que depende
del filtro del usuario. La traducción SQL→DAX está documentada con el número de validación
de cada medida en [`01_sql_a_dax.md`](proyectos/03_powerbi/01_sql_a_dax.md).

[Ver el proyecto →](proyectos/03_powerbi/)

---

### 4. Control de inventario de un bar · análisis con datos reales ★

<!-- COMPLETAR cuando termines P4 -->

Análisis de control de inventario sobre datos reales de la barra donde trabajo:
**73 insumos, 24 tragos en carta, 26 semanas**. Construí el **reporte de variación**
—el cálculo de lo que debería haberse consumido contra lo que realmente se consumió—
que es el análisis que mide **pérdida** y no venta.

**El hallazgo:** [COMPLETAR]

**Por qué este proyecto es distinto a los otros tres:** usa datos que no están
disponibles públicamente, sobre un negocio que conozco por dentro. Los otros proyectos
demuestran que sé usar las herramientas; este demuestra que sé encontrar el problema.

> **Nota sobre los datos:** publicados de forma anonimizada (ratios y porcentajes, sin
> precios de compra, proveedores ni recetas). El detalle del criterio de anonimización
> está en el README del proyecto.

[Ver el proyecto →](proyectos/04_estrella/)

---

## Qué se publica y qué no

Este repositorio es el portafolio: **proyectos, datos y los scripts que los generan.**

No están publicados —aunque sí en mi entorno de trabajo— mi plan de estudio personal,
mis notas, mis guías de aprendizaje y mi material de búsqueda laboral. Es deliberado:

> **Un portafolio muestra trabajo terminado, no apuntes de estudio.**

Y hay una razón práctica: mi material de búsqueda laboral incluye notas sobre cómo
conversar con mi empleador actual sobre cambiar de función. Eso no va en un repositorio
público mientras sigo trabajando ahí.

Tampoco se publican las claves de respuestas de los ejercicios ni las bases de datos
generadas: las primeras son autoevaluación, y las segundas se reconstruyen con un comando.

---

## Cómo reproducir los datasets

Los datasets son **sintéticos y reproducibles**: tienen semilla fija, así que dos
ejecuciones producen exactamente el mismo archivo. No dependen de ninguna descarga
externa.

```bash
python scripts/generar_dataset_p1.py      # retail: 2.935 filas, 12 defectos de calidad
python scripts/generar_dataset_p2.py      # retail: 7 tablas, 15 defectos de integridad
python scripts/crear_db_sqlite.py         # base SQLite lista para consultar
python scripts/generar_dataset_bar.py     # bar: 7 tablas, 5 causas de merma
```

Cada generador **verifica su propia salida**: re-lee el archivo escrito y comprueba que
los defectos inyectados coincidan exactamente con los detectados. Si la verificación
falla, el script termina con error en vez de dejar un dataset silenciosamente roto.

```bash
python scripts/verificar_p2_sqlite.py     # 15/15 consultas contra un motor SQL real
python scripts/verificar_calentamiento_sql.py  # 28/28 ejercicios resolubles
python scripts/verificar_bar_sql.py       # recupera las 5 causas de merma
python scripts/verificar_enlaces.py       # consistencia de los documentos
```

Los datasets se usan para **practicar análisis sobre problemas conocidos**: los defectos
están inyectados a propósito para que el ejercicio tenga una solución verificable.

---

## Sobre el uso de IA

Uso IA como tutor y revisor —para entender un concepto, para que critique una consulta
ya escrita, para generar casos de prueba— pero **el análisis, las decisiones y el código
de estos proyectos son míos**. Me parece la única forma de que un portafolio sirva: si no
puedo defender una decisión en una entrevista, ese trabajo no cuenta.

---

## Contacto

[tu@email.com] · [LinkedIn](https://linkedin.com/in/tu-perfil)

Abierto a roles de **Analista de Datos / Analista BI / Analista de Reportes**,
remoto o híbrido.
