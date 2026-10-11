# Manual de técnicas de Power Query

> **Qué es esto:** el "cómo se hace", no el "qué te falta". Los 12 tipos de problemas que
> tiene el dataset están en el [README del proyecto](README.md). Acá está **la herramienta
> para resolverlos**, con las trampas que hacen perder horas.
>
> Esto no es la clave de respuestas. Podés leerlo entero sin arruinarte el ejercicio.

---

## 0 · Tu entorno (verificado)

| | |
|---|---|
| Excel | **Office 365 ProPlus x64, en español (`es-es`)** — `C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE` |
| Power Query | ✅ **Integrado en Excel** (`Datos → Obtener datos`) |
| Power Pivot | ✅ Disponible (add-in presente) |
| Power View / Power Map | ✅ Disponibles |

**No necesitás instalar nada para el Proyecto 1.** Estás listo.

Pero el `es-es` tiene una consecuencia directa sobre cómo Power Query lee los datos, y es
tan importante que le dediqué una sección entera más abajo (**§6b**). Resumen: tu
configuración regional **te va a mentir en 881 valores** sin dar ningún error visible.

> **Podés comprobar todo lo que este manual afirma sobre tus datos** ejecutando:
> ```bash
> python scripts/diagnosticar_separadores_p1.py
> ```
> Te muestra los formatos numéricos que conviven, cuántos errores vas a ver en cada
> columna y por qué. Los números de este manual están medidos, no estimados.

---

## 1 · Por qué Power Query cambia todo (y por qué no es "Excel avanzado")

La diferencia entre una fórmula de Excel y Power Query no es de potencia: es de **naturaleza**.

| | Fórmulas de Excel | Power Query |
|---|---|---|
| Dónde vive el proceso | En las celdas, mezclado con los datos | **Aparte**, en una lista de pasos con nombre |
| Si cambia el archivo de origen | Se rompe todo | **Un clic y se re-ejecuta entero** |
| Si cambian los encabezados | Las referencias apuntan a cualquier lado | Se ajusta y listo |
| Cómo se audita | Leyendo fórmulas celda por celda | Leyendo una lista de pasos |
| Repetible | No | **Sí** |

Un reporte hecho con fórmulas es un **artefacto**: existe una vez. Un proceso de Power Query
es un **programa**: se vuelve a ejecutar cuando querés, sobre datos nuevos, y da lo mismo.

Esa es la razón por la que un pipeline mal hecho pero re-ejecutable vale más que un análisis
brillante hecho a mano una vez. Y es exactamente lo que un empleador quiere comprar.

**Consecuencia práctica para vos:** no persigas el análisis perfecto. Perseguí el proceso que
otro puede correr sin vos.

---

## 2 · La interfaz en 4 zonas

Al abrir Power Query (`Datos → Obtener datos → Iniciar el Editor de Power Query`):

```
┌──────────────────────────────────────────────────────────────────┐
│  CINTA DE OPCIONES — Inicio | Transformar | Agregar columna | Ver │
├──────────────────────┬───────────────────────────────────────────┤
│                      │                                           │
│  CONSULTAS           │   TABLA DE DATOS                          │
│  (panel izquierdo)   │   (el resultado de todos los pasos)       │
│                      │                                           │
│  Acá viven tus       │   Mientras más pasos agregás, esto        │
│  consultas. Podés    │   cambia. Es la vista previa, no el dato  │
│  tener varias.       │   original.                               │
│                      │                                           │
├──────────────────────┴───────────────────────────────────────────┤
│  PASOS APLICADOS — la lista de lo que hiciste, en orden.          │
│  Acá se puede deshacer cualquier paso, o borrarlo, sin rehacer    │
│  los siguientes. Es el corazón de Power Query.                    │
└──────────────────────────────────────────────────────────────────┘
```

**La zona que importa es la de abajo.** Cada cosa que hacés agrega un paso con nombre. Podés
renombrarlos (recomendado: `Limpiar espacios`, no `Cambió el tipo1`), borrarlos, reordenarlos.

**Regla de oro:** un paso sin nombre descriptivo es un paso que no vas a entender en dos
semanas. Renombralos a medida que avanzás.

---

## 3 · El orden de trabajo (siempre el mismo)

Hacer las cosas fuera de orden es la causa #1 de procesos que se rompen:

```
1. REVISAR       ¿Qué tengo? Distribución de columnas, valores únicos, tipos detectados.
                 NO TOCAR NADA TODAVÍA.
2. TIPAR         Convertir los tipos (fecha, número, texto) con la configuración
                 regional correcta. Antes de limpiar texto.
3. LIMPIAR       Espacios, mayúsculas, categorías, nulos, duplicados.
4. COMBINAR      Merge con catálogos, agregar columnas calculadas.
5. CARGAR        A la hoja de Excel o al modelo de datos.
```

**Por qué tipar antes de limpiar:** si limpiás texto y después convertís a fecha, un valor
que no parsea te rompe la consulta entera y perdés el trabajo hecho. Y al revés: no podés
limpiar bien un número que todavía es texto.

---

## 4 · Los 10 diagnósticos que corrés ANTES de tocar nada

En Power Query, sobre la tabla cargada. Estos son los que hacen visible lo invisible.

| # | Qué mirar | Dónde | Qué te dice |
|---|---|---|---|
| 1 | **Cardinalidad de cada columna de texto** | `Transformar → Grupo → Estadísticas de columna → Recuento de valores distintos` | Cuántos valores únicos hay. Si `Categoria` tiene **48** valores, algo está mal |
| 2 | **Recuento de filas** | Barra de estado inferior | Cuántas filas tenés. Anotalo: es tu "antes" |
| 3 | **Perfil de columnas** | `Ver → Perfil de columna` | Histograma y % de valores válidos/distintos/error por columna |
| 4 | **Calidad de columna** | `Ver → Calidad de columna` | Qué % de cada columna es válido, distinto, error o vacío |
| 5 | **Distribución de columnas** | `Ver → Distribución de columna` | Los 10 valores que más se repiten. Ideal para ver variantes de escritura |
| 6 | **Nulos reales vs texto** | Filtrar y buscar `N/A`, `-`, vacío | Un nulo escrito como texto es peor que un nulo: no lo detecta nada |
| 7 | **Rango de fechas** | Ordenar la columna de fecha | Si el mínimo es 1900 o el máximo 2030, hay basura |
| 8 | **Suma de una columna numérica** | Clic derecho en el encabezado | Para comparar antes/después y detectar inflado de JOINs |
| 9 | **Errores** | `Inicio → Quitar filas → Quitar errores` (mirá antes de aplicar) | Cuántos valores no convierten |
| 10 | **Duplicados** | `Inicio → Quitar filas → Quitar duplicados` (mirá el recuento que ofrece) | Si te dice "se quitarán N filas", ese N es tu respuesta |

> **El más útil de todos es el #4 (Calidad de columna).** Te dice, columna por columna, qué
> porcentaje de valores son válidos y cuántos distintos hay. Es un diagnóstico completo en
> una vista, y casi nadie lo usa.

---

## 5 · Las 10 técnicas

### T1 · Convertir tipos (y la trampa de la configuración regional)

**Dónde:** clic en el ícono de tipo a la izquierda del encabezado, o
`Transformar → Tipo de datos`.

**La trampa:** si la columna usa **coma decimal** (`1.234,56`) y convertís con la
configuración regional en inglés, Power Query la interpreta mal o la deja como texto.
**No da error: da un número equivocado.**

**Solución:** `Inicio → Tipo de datos → Usar configuración regional…` → elegí
**Español (Argentina)** o el que corresponda. Ese diálogo te deja fijar **de una vez** el
tipo y la configuración regional. Es el que tenés que usar para la columna de precios.

> **Regla:** usá `Usar configuración regional` siempre que la columna tenga números con
> separadores o fechas con barras. El tipo de dato solo, sin configuración regional,
> asume la del sistema.

### T2 · Quitar espacios (Recortar y Limpiar)

**Dónde:** `Transformar → Formato → Recortar` y `Limpiar`.

- **Recortar** quita espacios al inicio y al final. Un espacio invisible al final hace que
  `"Lácteos"` y `"Lácteos "` sean dos valores distintos.
- **Limpiar** quita caracteres de control no imprimibles.

**La trampa que ninguna de las dos resuelve:** **espacios internos dobles** (`"Carla  Duarte"`)
y el carácter **NBSP** (`\xa0`, "espacio duro"). Recortar no los toca.

**Cómo se detectan y arreglan:**
- Para espacios dobles: `Transformar → Reemplazar valores` → buscar `"  "` (dos espacios),
  reemplazar por `" "` (uno). A veces hay que repetirlo hasta que no cambie nada.
- Para NBSP: es invisible. Lo detectás porque dos valores que se ven idénticos no se agrupan
  ni hacen Merge entre sí. Se reemplaza con `Transformar → Reemplazar valores`, pero tenés
  que poder **pegar** el carácter: copialo desde una celda que lo tenga.

> **Este es el error más frustrante de Power Query:** un Merge que "debería funcionar" y
> devuelve nulos, porque una de las claves tiene un espacio invisible. Si un Merge falla sin
> razón aparente, la causa es casi siempre esta.

### T3 · Quitar duplicados

**Dónde:** seleccioná las columnas que definen la unicidad → `Inicio → Quitar filas → Quitar duplicados`.

**La decisión de negocio:** dos filas con el mismo `ID_Pedido` pero distinto `Total` **no son
duplicados**: son un conflicto. Quitar duplicados por todas las columnas elimina solo las
idénticas; por una sola columna, te quedás con una arbitraria y perdés información.

**Lo correcto:** primero contar los conflictos (`Agrupar por` → `Todas las filas` → mirar),
después decidir. Y **escribir la decisión**.

### T4 · Estandarizar categorías

**Dónde:** `Transformar → Formato → Capitalizar cada palabra` + `Reemplazar valores`.

El problema: `"LÁCTEOS"`, `"lácteos"`, `"Lacteos"`, `" Lácteos"` son cuatro valores que
deberían ser uno. Diagnóstico: **columna `Categoria` con 48 valores distintos cuando debería
tener 8.**

**El orden que funciona:**
1. `Recortar` (saca espacios de los bordes)
2. Reemplazar espacios dobles
3. `Capitalizar cada palabra` (unifica mayúsculas)
4. **Revisar de nuevo el recuento de distintos** → ¿quedan variantes? Suelen ser tildes
   (`Lacteos` vs `Lácteos`). Se arreglan con `Reemplazar valores` explícito.

> **Cuidado con `Capitalizar cada palabra`:** convierte `"LÁCTEOS"` → `"Lácteos"`, pero
> `"LACTEOS"` (sin tilde) → `"Lacteos"`. No agrega tildes. Las variantes sin tilde necesitan
> reemplazo manual.

### T5 · Tratar nulos encubiertos

Un nulo puede estar escrito de seis formas: vacío, `N/A`, `-`, `SIN DATO`, `(en blanco)`.

**Dónde:** `Transformar → Reemplazar valores` → buscar cada variante, reemplazar por `null`
(en Power Query se escribe `null`, no "vacío").

**Por qué importa escribirlo como `null` y no como vacío:** un `null` real se comporta como
nulo en todas las operaciones (no suma, no cuenta, se puede filtrar). Un texto vacío **sí
cuenta** en un `COUNT` y te infla los totales.

Después: `Inicio → Quitar filas → Quitar filas vacías` si querés eliminarlas, o dejarlas como
`null` si la fila tiene otra información útil. **Es una decisión de negocio, no técnica.**

### T6 · Filtrar errores (y por qué no hay que borrarlos sin mirar)

**Dónde:** `Inicio → Quitar filas → Quitar errores`.

**Nunca apliques esto sin mirar primero.** Los errores suelen ser las filas que más
información te dan: son exactamente las que no encajan. La técnica correcta:

1. `Agregar columna → Columna personalizada` con `try ... otherwise null` para **capturar**
   el valor problemático en una columna nueva, en vez de perderlo.
2. Filtrar los errores **después** de haberlos contado y clasificado.

### T7 · Combinar consultas (Merge) contra un catálogo

**Dónde:** `Inicio → Combinar consultas`.

**Cuándo se usa:** cuando tenés una tabla de referencia (el catálogo de sucursales con su
región oficial) y querés traer ese dato en vez de corregirlo a mano.

**La diferencia conceptual, que es lo importante:**

| Enfoque | Qué pasa cuando aparece un valor nuevo |
|---|---|
| Corregir a mano (`Reemplazar valores`) | Hay que agregar otro reemplazo, a mano, otra vez |
| **Merge contra catálogo** | El valor nuevo se resuelve solo si está en el catálogo |

Tenés un catálogo en `datos/P1_catalogo_sucursales.csv`. **Usalo.** Es la diferencia entre
resolver el problema de hoy y resolver el problema para siempre.

**Tipos de combinación (`Tipo de combinación`):**
- `Combinación externa izquierda` (Left Outer) — conserva todas las filas de la izquierda.
  Es la que querés para traer datos de un catálogo.
- `Combinación interna` (Inner) — solo las que coinciden. **Úsala solo si querés descartar
  las que no coinciden.**
- `Anti izquierda` (Left Anti) — las que **no** tienen coincidencia. **Esta es la que sirve
  para encontrar los problemas.**

> **La trampa:** si el Merge devuelve `null` en la columna del catálogo, significa que la
> clave no coincidió. **Ese `null` no es un error: es el hallazgo.** Contalo antes de
> arreglarlo.

### T8 · Columna personalizada (recalcular)

**Dónde:** `Agregar columna → Columna personalizada`.

**Cuándo:** cuando el valor que necesitás no está en ninguna columna y hay que calcularlo.

La regla que hay que aplicar siempre: **no confíes en una columna de importe que viene de un
sistema viejo. Recalculala y comparala.**

```
[Cantidad] * [Precio] * (1 - [Descuento])
```

Después: una columna que compare el recalculado con el original, y un filtro para ver
cuántas filas no coinciden. Ese número es el hallazgo.

### T9 · Agrupar (Group By)

**Dónde:** `Inicio → Agrupar por`.

Es el `GROUP BY` de SQL. Dos usos en limpieza:

1. **Detectar duplicados y conflictos:** agrupar por la clave y agregar `Recuento de filas`.
   Las que tengan más de 1 son tu problema.
2. **Consolidar:** si hay filas repetidas legítimas (mismo pedido, varias líneas), agrupar
   por pedido y sumar.

**Y la operación avanzada:** `Agrupar por → Operación: Todas las filas`. Te deja una columna
con las filas completas de cada grupo, para inspeccionar los conflictos uno por uno.

### T10 · Separar una decisión en una consulta aparte

**Dónde:** clic derecho en una consulta → `Duplicar` o `Referencia`.

**Cuándo usarlo:** cuando un problema no tiene solución única. Las devoluciones son el caso
típico: no se borran ni se dejan, **se separan**. Una consulta `Ventas` y otra `Devoluciones`,
y ambas salen de la misma consulta limpia.

**Por qué es la marca de un profesional:** cuando el gerente pregunte "¿y por qué el total no
incluye esos?", la respuesta ya está modelada. No estás improvisando.

---

## 6 · La trampa más importante del dataset: fechas ambiguas

Esta merece su propia sección porque **no da ningún error visible**.

### El problema

El dataset mezcla cuatro formatos de fecha, y dos de ellos son **indistinguibles**:

```
15/03/2024   -> ¿15 de marzo (dd/mm) o... no: 15 no puede ser un mes. Solo dd/mm.
03/04/2024   -> 3 de abril (dd/mm)  ó  4 de marzo (mm/dd).  ← AMBIGUA
```

Las fechas donde el primer número es mayor a 12 son **inequívocamente** `mm/dd`. Y en este
dataset **existen**: hay 36 filas así. Eso **prueba** que el formato estadounidense está
presente en los datos.

Y si el formato estadounidense está presente, entonces **las ambiguas también pueden serlo**.

### Por qué es grave

Si Power Query interpreta `03/04/2024` como 4 de marzo cuando en realidad es 3 de abril,
tus fechas quedan corridas. Y como afecta a un subconjunto de las filas, **los totales por
mes quedan mal de una forma que no se ve**: no hay error, no hay nulo, solo números
equivocados. Un análisis mensual hecho sobre eso está mal y no lo podés saber.

**Es el peor tipo de error de datos: el que no avisa.**

### Qué vas a ver con TU configuración regional (es-ES)

Esto está medido, no estimado. Con `es-ES`, Power Query lee `A/B/aaaa` como **día/mes**:

| | |
|---|---|
| Valores en **Error** al convertir `Fecha` | **49** |
| ↳ de esos, fechas `mm/dd` con día > 12 | 36 |
| ↳ de esos, centinelas explícitos | 13 |
| Fechas que **convierten bien pero están mal** | 1 (el `1900-01-01`) |

> **Los 49 errores son tu mejor pista, no un problema.** Aparecen exactamente porque el
> formato estadounidense existe en los datos. Si Power Query no te diera ningún error, no
> podrías saber que el problema existe — y ahí sí estarías perdido.

### Cómo se detecta

1. Ordená la columna de fecha y mirá el mínimo y el máximo. ¿Hay años fuera del negocio?
2. `Calidad de columna` sobre la fecha: ¿qué % convierte bien?
3. **Buscá específicamente fechas con el primer número > 12.** Si hay una sola, el formato
   `mm/dd` existe en los datos.
4. Contá las ambiguas (donde los dos números son ≤ 12).

### Cómo se resuelve (y por qué no hay solución automática)

**No la hay.** Ninguna herramienta puede adivinar la intención de `03/04/2024`. Lo que sí
se puede hacer, y es lo profesional:

1. **Cuantificar:** "hay N fechas ambiguas sobre un total de M (x%)".
2. **Decidir con criterio:** si el resto de los datos es `dd/mm` y las ambiguas son el 2%,
   interpretarlas como `dd/mm` es defendible. **Escribilo.**
3. **Evaluar el impacto:** ¿cambia alguna conclusión? Corré el análisis con las dos
   interpretaciones sobre las ambiguas y mirá si el resultado de negocio se mueve. Si no se
   mueve, el problema es cosmético. Si se mueve, tenés que resolverlo fila por fila con
   alguna fuente externa.
4. **Documentar la limitación** en el README del proyecto, en la sección "Limitaciones".

> **Esto, escrito en tu README, vale más que cualquier gráfico.** Dice: *"sé que existe este
> problema, lo cuantifiqué, decidí esto, y sé cuánto puede afectar mi conclusión"*. Eso es un
> analista. Un gráfico lindo lo hace cualquiera.

---

## 6b · La trampa de los separadores decimales (y por qué tu locale te miente)

Esta es la trampa más peligrosa del dataset, más que las fechas, porque **el resultado
puede no dar ningún error: da un número 100 veces más grande.**

### El problema

En la misma columna de precios conviven **dos formatos numéricos**, y el mismo carácter
—el punto— significa dos cosas distintas:

| Formato | Ejemplo | El punto es… | Filas |
|---|---|---|---|
| Español | `1.234,56` | separador de **miles** | **1832** |
| Español simple | `984,76` | (sin punto) | 222 |
| Inglés | `1554.41` | separador **decimal** | **881** |

> **Detalle que vas a notar:** entre los 881, algunos tienen un solo decimal (`5179.8` en
> lugar de `5179.80`). Pasa cuando un sistema exporta números sin formatear. No es un
> error, pero te dice algo: **la cantidad de decimales tampoco es consistente**, así que no
> te apoyes en "siempre hay dos decimales" para detectar el formato.

**No existe una configuración regional que sirva para los dos.** Probá las dos:

| Locale | `1.234,56` | `1554.41` |
|---|---|---|
| **es-ES** (el tuyo) | ✅ 1234,56 | ❌ el punto se lee como miles → **Error o valor ×100** |
| en-US | ❌ Error o texto | ✅ 1554.41 |

### Por qué es tan peligroso

Con tu locale español, `1554.41` puede interpretarse como **155441**. Sin error, sin
advertencia, sin nulo. Y no lo vas a notar, porque un precio de 155.441 parece
perfectamente plausible en un dataset con inflación.

**Consecuencia:** si no lo detectás, tu facturación total va a dar un número enorme y vas a
escribir un análisis sobre él. Es exactamente el tipo de error que hace que un gerente
pierda la confianza en el área de datos para siempre.

> **Y esto no es un defecto "de juguete" del dataset.** Es lo que pasa en la vida real
> cuando una empresa tiene dos sistemas que exportan con configuración regional distinta,
> o cuando el área de sistemas cambió la configuración a mitad de camino. Le pasa a
> cualquiera que trabaje con datos de verdad.

### Cómo se detecta

1. **Mirá la columna como texto, no como número.** Ordenala alfabéticamente y vas a ver
   valores con coma y valores con punto.
2. `Calidad de columna` sobre el precio: si hay errores, ahí están.
3. **Buscá el patrón:** ¿algún valor tiene punto Y coma? Ese es formato español. ¿Alguno
   tiene punto y **ninguna** coma? Ese es formato inglés.
4. Contá cada grupo. Si los dos existen, tenés el problema.

### Cómo se resuelve (la receta correcta)

**La clave: normalizar el TEXTO antes de convertir el TIPO.** No pelees con la
configuración regional; hacé que los datos sean siempre del mismo formato primero.

**Paso 1.** Asegurate de que la columna está como **Texto**.

**Paso 2.** `Agregar columna → Columna personalizada`, con este código:

```
if Text.Contains([#"Precio_Unitario ($)"], ",")
then Text.Replace(Text.Replace([#"Precio_Unitario ($)"], ".", ""), ",", ".")
else [#"Precio_Unitario ($)"]
```

Qué hace, en castellano:

> *Si el valor tiene coma (o sea, es formato español), primero borrale todos los puntos
> (que son separadores de miles) y después cambiá la coma por un punto. Si no tiene coma
> (formato inglés), dejàlo como está.*

Resultado: **todos** los valores quedan en formato inglés (`1234.56`), sin importar cómo
venían.

**Paso 3.** Convertí esa columna nueva a **Número decimal**, usando
`Transformar → Tipo de datos → Usar configuración regional…` y eligiendo **Inglés (Estados
Unidos)**. Ahora sí, una sola configuración sirve para todo.

**Paso 4.** Renombrá la columna nueva a `Precio_Unitario`, borrá la original, y **repetí lo
mismo con la columna `Total`** (que tiene el mismo problema).

**Paso 5.** Verificá: la suma del precio debe dar un número del orden de decenas de miles
de millones, no de billones. Y el precio máximo debe ser coherente con lo que cuesta un
producto.

> ### ⚠️ El paso que casi todos saltean
> Si usás `Reemplazar valores` para borrar **todos** los puntos de la columna, vas a
> arruinar los 881 valores que usan el punto como decimal: `1554.41` → `155441`.
> **La normalización tiene que ser condicional.** Esa es toda la diferencia entre arreglar
> el problema y empeorarlo.

### La lección que te llevás

> **Nunca confíes en la conversión automática de tipos.** Antes de convertir, preguntate:
> *¿de dónde salió este archivo y con qué configuración regional se exportó?* Y después
> verificá el resultado contra un valor que sepas correcto.

Una columna bien convertida **da el mismo resultado sin importar el locale de quien la
procesa**. Si tu proceso depende del locale de tu máquina, no es un proceso: es una lotería.

---

## 7 · Cómo saber si terminaste (y que no te lo diga la clave)

Antes de abrir la clave de respuestas, corré estas comprobaciones **sobre tu resultado**:

| Comprobación | Cómo |
|---|---|
| Cardinalidad de textos | `Categoria` debe tener **8** valores únicos; `Sucursal`, 8; `Vendedor`, 12 (+ nulos) |
| Tipos | `Fecha` es Fecha. `Precio_Unitario` y `Total` son número decimal. Ninguna columna numérica es Texto |
| Rangos | Ninguna fecha fuera de 2023–2024. Ningún descuento fuera de 0–1. Ningún precio ≤ 0 |
| Importe recalculado | `Total` = `Cantidad × Precio × (1 − Descuento)` con tolerancia de 1 peso, **en todas las filas** |
| Sin espacios | Ninguna celda de texto empieza o termina con espacio |
| Sin errores | Ninguna columna tiene valores en Error |
| Recuento de filas | Coincide con el que anotaste al principio, menos los duplicados que quitaste |

**Si las siete pasan, terminaste.** Recién ahí abrí la clave y comparé los conteos con los
tuyos. Si coinciden, no tuviste suerte: **hiciste bien el trabajo de forma verificable.**

---

## 8 · Para ir más allá (no lo necesitás para P1)

- **Consultas de referencia vs duplicado:** `Referencia` usa la consulta anterior como
  fuente sin copiar los datos; `Duplicar` copia. Con muchas consultas encadenadas, la
  diferencia importa.
- **Parámetros:** `Inicio → Administrar parámetros`. Sirven para que un cambio (una ruta, un
  año) se haga en un solo lugar.
- **Funciones personalizadas:** si repetís la misma limpieza en varias consultas, se puede
  convertir en función. Es el paso de "usuario de Power Query" a "alguien que programa".
- **El lenguaje M:** todo lo que hacés con clics se escribe en M. `Inicio → Editor avanzado`
  te muestra el código. **No lo aprendas ahora**, pero miralo: te va a mostrar que Power Query
  es un lenguaje de programación, no un menú.
