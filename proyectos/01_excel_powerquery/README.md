# Proyecto 1 — Excel + Power Query

**Tesis:** *"Un reporte que antes tardaba 3 días de trabajo manual ahora se actualiza en 10 minutos."*

**Semanas:** 2–3

---

## Problema de negocio
_(Escribir ANTES de tocar los datos. Una o dos frases. ¿Quién sufre hoy por no tener este reporte a tiempo?)_
<!-- TODO -->

## Datos y fuentes
| Campo | Valor |
|---|---|
| Dataset | Ventas de una cadena de supermercados (sintético realista) |
| Origen | Generado con [`scripts/generar_dataset_p1.py`](../../scripts/generar_dataset_p1.py), semilla fija → reproducible |
| Filas × columnas | **2935 × 14** (2900 reales + 35 duplicados a detectar) |
| Periodo | 2023-01-01 a 2024-12-31 |
| Licencia | Sintético, uso libre |
| Guardado en | [`datos/P1_ventas_crudo.csv`](../../datos/P1_ventas_crudo.csv) + [`datos/P1_catalogo_sucursales.csv`](../../datos/P1_catalogo_sucursales.csv) |

> ⚠️ **No abras el archivo `datos/P1_DEFECTOS_clave_NO_ABRIR.md` hasta terminar.**
> Es la clave de respuestas: contiene los 12 defectos y cuántas filas afecta cada uno. Si lo leés antes, el ejercicio pierde todo su valor (y en una entrevista no vas a tener la clave al lado).
> Ese archivo es tu autoevaluación local y **no se publica** en el repositorio.

El dataset tiene **12 tipos de problemas de calidad** inyectados a propósito, del tipo que aparece en un export real de un sistema viejo. El ejercicio es dejarlo limpio y explicar cada decisión.

> 📘 **Antes de abrir Power Query, leé el [manual de técnicas](01_manual_powerquery.md).**
> Tiene el "cómo se hace" (las 10 técnicas, las trampas, los diagnósticos previos) sin
> spoilers: no dice qué filas tienen qué problema. Incluye una sección sobre la trampa
> más peligrosa del dataset — las **fechas ambiguas** — que no da ningún error visible.

## Proceso y decisiones
_(Capturas del editor de Power Query + explicación de cada paso. Sin capturas, el reclutador no puede verificar que el trabajo es tuyo.)_

1.
2.
3.

**Problemas de calidad encontrados:** duplicados / nulos / tipos / formatos de fecha / categorías inconsistentes / valores atípicos
- 
**Decisión tomada y por qué:**
- 

## Hallazgos
_(Mínimo 5. Cada uno con número. "Las ventas cayeron 12%" no sirve; "las ventas cayeron 12% en la región Sur, concentradas en 3 SKUs que representan el 60% de la caída" sí.)_

1.
2.
3.
4.
5.

## Recomendaciones
_(Qué debería hacer el negocio el próximo mes, a partir de los hallazgos.)_

1.
2.

## Limitaciones
_(Qué NO puede concluir este análisis. Esto da credibilidad, no la quita.)_
- 

## Qué haría con más tiempo
- 

## Prueba de defensa
- [ ] Puedo explicar cada paso de Power Query sin abrir el archivo
- [ ] Puedo justificar cada decisión de limpieza
- [ ] Puedo mencionar un hallazgo que contradiga mi hipótesis inicial
