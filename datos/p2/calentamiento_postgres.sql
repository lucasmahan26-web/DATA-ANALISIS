\echo === CALENTAMIENTO SQL EN POSTGRESQL, 28 EJERCICIOS ===
SET client_encoding TO 'UTF8';

\echo --- Ejercicio 1: Primeras 20 filas de ventas
SELECT * FROM ventas LIMIT 20;

\echo --- Ejercicio 2: Solo id_venta, fecha_venta e importe_neto
SELECT id_venta, fecha_venta, importe_neto FROM ventas LIMIT 100;

\echo --- Ejercicio 3: Las 10 ventas de mayor importe
SELECT id_venta, importe_neto FROM ventas ORDER BY importe_neto DESC LIMIT 10;

\echo --- Ejercicio 4: Ventas del 15/03/2024
SELECT COUNT(*) FROM ventas WHERE fecha_venta = '2024-03-15';

\echo --- Ejercicio 5: Ventas con importe > 50.000, de mayor a menor
SELECT id_venta, importe_neto FROM ventas WHERE importe_neto > 50000 ORDER BY importe_neto DESC LIMIT 100;

\echo --- Ejercicio 6: Ventas de todo marzo 2024
SELECT COUNT(*) FROM ventas WHERE fecha_venta BETWEEN '2024-03-01' AND '2024-03-31';

\echo --- Ejercicio 7: Medios de pago
SELECT id_medio_pago, descripcion FROM medios_pago ORDER BY id_medio_pago;

\echo --- Ejercicio 8: Productos inactivos
SELECT id_producto, nombre_producto FROM productos WHERE activo = 'N';

\echo --- Ejercicio 9: Total de filas de ventas
SELECT COUNT(*) AS filas FROM ventas;

\echo --- Ejercicio 10: Suma total de importe_neto
SELECT ROUND(SUM(importe_neto), 2) AS total FROM ventas;

\echo --- Ejercicio 11: Promedio, minimo y maximo de importe_neto
SELECT ROUND(AVG(importe_neto), 2) AS promedio, ROUND(MIN(importe_neto), 2) AS minimo, ROUND(MAX(importe_neto), 2) AS maximo FROM ventas;

\echo --- Ejercicio 12: Ventas por turno de vendedor
SELECT vd.turno, COUNT(*) AS ventas FROM ventas v JOIN vendedores vd ON v.id_vendedor = vd.id_vendedor GROUP BY vd.turno ORDER BY ventas DESC;

\echo --- Ejercicio 13: Ventas por region de sucursal
SELECT s.region, COUNT(*) AS ventas FROM ventas v JOIN sucursales s ON v.id_sucursal = s.id_sucursal GROUP BY s.region ORDER BY ventas DESC;

\echo --- Ejercicio 14: Facturacion por anio y mes
SELECT EXTRACT(YEAR FROM fecha_venta)::int AS anio, EXTRACT(MONTH FROM fecha_venta)::int AS mes, ROUND(SUM(importe_neto), 2) AS facturacion FROM ventas GROUP BY 1, 2 ORDER BY 1, 2;

\echo --- Ejercicio 15: Top 5 productos por unidades vendidas
SELECT id_producto, SUM(cantidad) AS unidades FROM ventas GROUP BY id_producto ORDER BY unidades DESC LIMIT 5;

\echo --- Ejercicio 16: Tipos de cliente con mas de 200 ventas (HAVING)
SELECT c.tipo_cliente, COUNT(*) AS ventas FROM ventas v JOIN clientes c ON v.id_cliente = c.id_cliente GROUP BY c.tipo_cliente HAVING COUNT(*) > 200 ORDER BY ventas DESC;

\echo --- Ejercicio 17: Cantidad de pedidos distintos
SELECT COUNT(DISTINCT id_pedido) AS pedidos FROM ventas;

\echo --- Ejercicio 18: Regiones distintas
SELECT DISTINCT region FROM sucursales ORDER BY region;

\echo --- Ejercicio 19: Ventas con id_medio_pago 1 o 5
SELECT COUNT(*) AS con_in FROM ventas WHERE id_medio_pago IN (1, 5);

\echo --- Ejercicio 20: Productos cuyo nombre contiene 'Leche'
SELECT id_producto, nombre_producto FROM productos WHERE nombre_producto LIKE '%Leche%';

\echo --- Ejercicio 21: Clasificar ventas por rango de importe
SELECT CASE WHEN importe_neto < 10000 THEN 'chico' WHEN importe_neto <= 50000 THEN 'mediano' ELSE 'grande' END AS rango, COUNT(*) AS ventas FROM ventas GROUP BY rango ORDER BY ventas DESC;

\echo --- Ejercicio 22: Venta + nombre de producto
SELECT v.id_venta, v.fecha_venta, p.nombre_producto, v.importe_neto FROM ventas v JOIN productos p ON v.id_producto = p.id_producto LIMIT 50;

\echo --- Ejercicio 23: Facturacion por categoria (3 tablas)
SELECT c.nombre_categoria, ROUND(SUM(v.importe_neto), 2) AS facturacion FROM ventas v JOIN productos p ON v.id_producto = p.id_producto JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre_categoria ORDER BY facturacion DESC;

\echo --- Ejercicio 24: INNER vs LEFT JOIN sobre sucursales
SELECT (SELECT COUNT(*) FROM ventas v JOIN sucursales s ON v.id_sucursal = s.id_sucursal) AS con_inner_join, (SELECT COUNT(*) FROM ventas v LEFT JOIN sucursales s ON v.id_sucursal = s.id_sucursal) AS con_left_join, (SELECT COUNT(*) FROM ventas) AS total_filas;

\echo --- Ejercicio 25: Vendedores con sus ventas, incluidos los que no vendieron
SELECT vd.nombre_vendedor, ROUND(COALESCE(SUM(v.importe_neto), 0), 2) AS total FROM vendedores vd LEFT JOIN ventas v ON vd.id_vendedor = v.id_vendedor GROUP BY vd.id_vendedor, vd.nombre_vendedor ORDER BY total DESC LIMIT 15;

\echo --- Ejercicio 26: Mes de mayor facturacion por sucursal (ROW_NUMBER)
WITH por_mes AS (SELECT id_sucursal, TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, SUM(importe_neto) AS total FROM ventas GROUP BY 1, 2), rank AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY id_sucursal ORDER BY total DESC) AS rn FROM por_mes) SELECT id_sucursal, mes, ROUND(total, 2) AS total FROM rank WHERE rn = 1 ORDER BY id_sucursal;

\echo --- Ejercicio 27: Variacion porcentual mes a mes (LAG)
WITH por_mes AS (SELECT TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, SUM(importe_neto) AS total FROM ventas GROUP BY 1) SELECT mes, ROUND(total, 2) AS total, ROUND(100.0 * (total - LAG(total) OVER (ORDER BY mes)) / LAG(total) OVER (ORDER BY mes), 2) AS var_pct FROM por_mes ORDER BY mes;

\echo --- Ejercicio 28: Acumulado del anio (running total)
WITH por_mes AS (SELECT TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, SUM(importe_neto) AS total FROM ventas GROUP BY 1) SELECT mes, ROUND(total, 2) AS total, ROUND(SUM(total) OVER (ORDER BY mes ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS acumulado FROM por_mes ORDER BY mes;
