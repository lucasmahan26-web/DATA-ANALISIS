-- =============================================================================
-- P2_01_crear_tablas.sql  —  Proyecto 2 (SQL / PostgreSQL)
-- =============================================================================
-- Crea las 7 tablas del modelo SIN claves primarias ni foráneas.
--
-- ¿Por qué sin constraints? Porque si las agregás ahora, PostgreSQL te va a
-- RECHAZAR la carga de los CSV: los datos tienen claves huérfanas y PK
-- duplicadas a propósito. Ese error es parte del ejercicio, no un obstáculo.
--
-- Orden completo:
--   1. Este script  (tablas sin constraints)
--   2. Cargar los 7 CSV de datos/p2/
--   3. Diagnosticar y limpiar       ← el trabajo real
--   4. P2_02_agregar_constraints.sql (PK y FK, al final)
--
-- Ejecutar en la base `analisis`:
--   psql -U postgres -d analisis -f scripts/P2_01_crear_tablas.sql
-- =============================================================================

DROP TABLE IF EXISTS ventas       CASCADE;
DROP TABLE IF EXISTS vendedores   CASCADE;
DROP TABLE IF EXISTS productos    CASCADE;
DROP TABLE IF EXISTS clientes     CASCADE;
DROP TABLE IF EXISTS sucursales   CASCADE;
DROP TABLE IF EXISTS categorias   CASCADE;
DROP TABLE IF EXISTS medios_pago  CASCADE;

-- ---------------------------------------------------------------- dimensiones
CREATE TABLE categorias (
    id_categoria      integer,
    nombre_categoria  text,
    departamento      text
);

CREATE TABLE productos (
    id_producto       integer,
    nombre_producto   text,
    id_categoria      integer,
    precio_lista      numeric(12,2),
    activo            char(1),
    fecha_alta        date
);

CREATE TABLE sucursales (
    id_sucursal       integer,
    nombre_sucursal   text,
    region            text,
    provincia         text,
    zona_comercial    text,
    fecha_apertura    date
);

CREATE TABLE vendedores (
    id_vendedor       integer,
    nombre_vendedor   text,
    id_sucursal       integer,
    fecha_ingreso     date,
    turno             text
);

CREATE TABLE clientes (
    id_cliente        integer,
    razon_social      text,
    tipo_cliente      text,
    ciudad            text,
    provincia         text,
    fecha_alta        date
);

CREATE TABLE medios_pago (
    id_medio_pago     integer,
    descripcion       text
);

-- ------------------------------------------------------------- tabla de hechos
-- OJO: los nombres de columna con guion bajo son los que espera el COPY.
CREATE TABLE ventas (
    id_venta          integer,
    id_pedido         text,
    fecha_venta       date,
    id_producto       integer,
    id_sucursal       integer,      -- tiene NULLs a propósito
    id_vendedor       integer,
    id_cliente        integer,
    id_medio_pago     integer,
    cantidad          integer,
    precio_unitario   numeric(12,2),
    descuento         numeric(6,3),
    importe_neto      numeric(14,2)
);

-- =============================================================================
-- CARGA DE LOS CSV
-- =============================================================================
-- Opción A — psql con \copy (desde la raíz del repo). No requiere superusuario:
--
--   \copy categorias   FROM 'datos/p2/categorias.csv'   WITH (FORMAT csv, HEADER true, NULL '')
--   \copy productos    FROM 'datos/p2/productos.csv'    WITH (FORMAT csv, HEADER true, NULL '')
--   \copy sucursales   FROM 'datos/p2/sucursales.csv'   WITH (FORMAT csv, HEADER true, NULL '')
--   \copy vendedores   FROM 'datos/p2/vendedores.csv'   WITH (FORMAT csv, HEADER true, NULL '')
--   \copy clientes     FROM 'datos/p2/clientes.csv'     WITH (FORMAT csv, HEADER true, NULL '')
--   \copy medios_pago  FROM 'datos/p2/medios_pago.csv'  WITH (FORMAT csv, HEADER true, NULL '')
--   \copy ventas       FROM 'datos/p2/ventas.csv'       WITH (FORMAT csv, HEADER true, NULL '')
--
-- Opción B — DBeaver: clic derecho en la tabla > "Import Data" > CSV.
--   Configurar: delimiter `,` · header = sí · quote `"` · encoding UTF-8 ·
--   y en la pestaña de columnas, mapear la cadena vacía a NULL para id_sucursal.
--
-- Opción C — COPY del servidor (requiere permisos y ruta absoluta):
--   COPY ventas FROM '/ruta/absoluta/datos/p2/ventas.csv'
--     WITH (FORMAT csv, HEADER true, NULL '');
--
-- Los CSV están en UTF-8 SIN BOM a propósito: el BOM rompería la primera
-- columna del COPY.
-- =============================================================================
