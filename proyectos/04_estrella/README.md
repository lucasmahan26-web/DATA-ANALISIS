# Proyecto 4 ★ — Control de inventario de un bar (datos reales)

**Tesis:** *El único proyecto que nadie más puede replicar, porque usa datos y conocimiento de dominio que solo yo tengo.*

**Semanas:** 11–12 (o antes, si tenés los datos a mano)

---

## Por qué este proyecto es fuerte (y no es una anécdota)

Soy bartender y tengo acceso al inventario del bar donde trabajo. A primera vista parece un
dataset pobre. **Es al revés.** Un bar tiene una propiedad analítica que casi ningún otro
negocio tiene:

> **Se puede calcular cuánto *deberías* haber consumido y compararlo con lo que *realmente*
> consumiste.** Eso se llama **reporte de variación**, y mide la pérdida, no la venta.

Un e-commerce no puede hacer esto. Una empresa de servicios no puede. Necesitás un inventario
físico que se cuenta dos veces — y yo estoy en el lugar donde eso pasa.

**Los 8 análisis posibles están en [`01_catalogo_analisis.md`](01_catalogo_analisis.md).**
El más valioso (y el objetivo) es el reporte de variación. Los de nivel base ya son publicables.

**Y hay un bonus:** este proyecto es *también* mi conversación de transferencia interna. Ver
[`02_diagnostico_y_privacidad.md`](02_diagnostico_y_privacidad.md).

---

## ⚠️ Antes de empezar: autorización

Son datos de mi empleador. Contienen precios de compra, proveedores, recetas y ventas —
información comercialmente sensible. **No publico nada sin permiso.**

El protocolo completo (orden correcto, texto para pedirlo, 3 niveles de anonimización) está en
[`02_diagnostico_y_privacidad.md`](02_diagnostico_y_privacidad.md#parte-1--autorización-y-anonimización).

Resumen: hago el análisis **para el bar** primero, se lo muestro a mi jefe, y **después** pido
permiso para publicar una versión anonimizada. Ratios y porcentajes sí; precios, proveedores y
recetas no.

---

## 🎯 Dataset de práctica (mientras consigo los datos reales)

No necesito los datos del bar para empezar a practicar las técnicas. Hay un dataset de
práctica con la **misma estructura** de una planilla de inventario de bar real, y con algo
que lo hace mucho mejor que cualquier dataset de Kaggle:

> **Tiene 5 causas de merma inyectadas con firma conocida.** El ejercicio es recuperarlas.
> Y el dataset está construido derivando los conteos del uso real, así que el reporte de
> variación **reconstruye exactamente lo inyectado**. Si no lo hiciera, el ejercicio no
> tendría solución.

| Archivo | Qué es |
|---|---|
| `datos/bar/analisis_bar.db` | **Base SQLite lista para abrir en DBeaver** (7 tablas) |
| `datos/bar/*.csv` | Las 7 tablas en crudo, por si querés cargarlas en PostgreSQL |
| `datos/bar/BAR_CLAVE_NO_ABRIR.md` | ⚠️ Spoiler local (no publicado): las 5 causas, los conteos y las consultas de verificación |

**Las 5 causas que hay que descubrir** (los detalles están en la clave, no acá):
over-pouring · robo · error de conteo · comp no registrado · remito no cargado.

**Las 7 tablas:** `insumos`, `carta`, `recetas`, `ventas`, `compras`, `conteos`, `calendario`.

**Lo que este ejercicio enseña y ningún tutorial enseña:**

1. **El robo no se busca por volumen, se busca por plata.** Ordenar por mililitros hace
   ganar a los mixers (volumen enorme, valor bajo) y esconde el whisky premium robado.
   Ordenar por pesos lo expone. Elegir la métrica correcta **es** el trabajo del analista.
2. **Un error de conteo se compensa al período siguiente; un comp no.** Los dos se ven como
   "un pico en una semana", y distinguirlos cambia la acción: recontar vs. investigar.
3. **La variación negativa también es un problema** (y no de sustancia, sino de papeleo).
4. **La trampa de `LAG()` con `WHERE`**: `WHERE` se evalúa *antes* que las funciones de
   ventana, así que filtrar la semana 0 en la misma consulta rompe el cálculo. Documentado
   en la clave.

> Al aplicar esto a los datos reales del bar, las 5 causas ya no van a estar inyectadas:
> van a estar ahí de verdad, y vas a saber cómo se ven.

---

## Problema de negocio
_(Escribir ANTES de tocar los datos. ¿Quién pierde plata hoy por no tener este análisis? ¿El dueño sabe cuánto se le pierde por mes?)_
<!-- TODO -->

## Diagnóstico de datos disponibles

Completar [`02_diagnostico_y_privacidad.md`](02_diagnostico_y_privacidad.md) (Parte 2) y anotar
acá el nivel alcanzado:

| Campo | Valor |
|---|---|
| Nivel alcanzado (🟢🟡🟠🔴) | |
| Análisis que puedo hacer | |
| Análisis que NO puedo hacer (y qué me falta) | |

## Datos y fuentes

| Campo | Valor |
|---|---|
| Origen | Inventario del bar donde trabajo (anonimizado) |
| Formato original | |
| Periodo cubierto | |
| Cantidad de insumos | |
| Autorización del empleador | ☐ pedida ☐ otorgada — fecha: ______ |
| Versión publicada | Anonimizada nivel ___ |

## Impacto medible

_(El "antes" se mide ANTES de intervenir. Si no lo medís al principio, no podés demostrar la mejora.)_

| Métrica | Antes | Después | Mejora |
|---|---|---|---|
| Variación / merma | | | |
| Pour cost del bar | | | |
| Tiempo de armado del reporte | | | |
| Conteos por período | | | |

## Proceso
1.
2.
3.

## Hallazgos
_(Mínimo 3, cada uno con número.)_

1.
2.
3.

## Recomendaciones
_(Qué debería hacer el bar, concretamente, a partir de los hallazgos.)_

1.
2.

## Limitaciones
_(Qué NO puede concluir este análisis. Esto da credibilidad, no la quita. Ejemplo: si no tengo POS por producto, el uso teórico es una estimación.)_
-

## Qué haría con más tiempo
-

## Prueba de defensa
- [ ] Puedo explicar la diferencia entre pour cost y variación sin dudar
- [ ] Puedo nombrar las 4 causas de variación **en orden** y por qué el orden importa
- [ ] Puedo contar el hallazgo principal en 3 minutos, con el número
- [ ] Puedo explicar cómo anonimicé los datos y por qué
- [ ] Sé decir qué NO puedo concluir con los datos que tengo
