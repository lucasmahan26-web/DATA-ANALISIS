-- =============================================================================
-- P2_02_agregar_constraints.sql  —  Proyecto 2 (SQL / PostgreSQL)
-- =============================================================================
-- Este es el script que ejecutás AL FINAL, cuando ya limpiaste los datos.
--
-- Es tu prueba objetiva: si alguna sentencia falla, todavía hay basura.
-- PostgreSQL te va a decir exactamente qué fila viola qué restricción.
-- Ese mensaje de error es la respuesta correcta, no un problema.
--
-- Ejecutar en la base `analisis`:
--   psql -U postgres -d analisis -f scripts/P2_02_agregar_constraints.sql
-- =============================================================================

-- ------------------------------------------------------- claves primarias
-- Falla si quedan id_venta duplicados.
ALTER TABLE categorias  ADD CONSTRAINT pk_categorias  PRIMARY KEY (id_categoria);
ALTER TABLE medios_pago ADD CONSTRAINT pk_medios_pago PRIMARY KEY (id_medio_pago);
ALTER TABLE sucursales  ADD CONSTRAINT pk_sucursales  PRIMARY KEY (id_sucursal);
ALTER TABLE productos   ADD CONSTRAINT pk_productos   PRIMARY KEY (id_producto);
ALTER TABLE vendedores  ADD CONSTRAINT pk_vendedores  PRIMARY KEY (id_vendedor);
ALTER TABLE clientes    ADD CONSTRAINT pk_clientes    PRIMARY KEY (id_cliente);
ALTER TABLE ventas      ADD CONSTRAINT pk_ventas      PRIMARY KEY (id_venta);

-- ------------------------------------------------------- claves foráneas
-- Cada una falla mientras queden huérfanos en la tabla de hechos.
ALTER TABLE productos
    ADD CONSTRAINT fk_productos_categoria
    FOREIGN KEY (id_categoria) REFERENCES categorias (id_categoria);

ALTER TABLE vendedores
    ADD CONSTRAINT fk_vendedores_sucursal
    FOREIGN KEY (id_sucursal) REFERENCES sucursales (id_sucursal);

ALTER TABLE ventas
    ADD CONSTRAINT fk_ventas_producto
    FOREIGN KEY (id_producto) REFERENCES productos (id_producto);

ALTER TABLE ventas
    ADD CONSTRAINT fk_ventas_sucursal
    FOREIGN KEY (id_sucursal) REFERENCES sucursales (id_sucursal);

ALTER TABLE ventas
    ADD CONSTRAINT fk_ventas_vendedor
    FOREIGN KEY (id_vendedor) REFERENCES vendedores (id_vendedor);

ALTER TABLE ventas
    ADD CONSTRAINT fk_ventas_cliente
    FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente);

ALTER TABLE ventas
    ADD CONSTRAINT fk_ventas_medio_pago
    FOREIGN KEY (id_medio_pago) REFERENCES medios_pago (id_medio_pago);

-- ------------------------------------------- reglas de negocio como constraints
-- Documentar una regla de negocio como CHECK es lo que convierte tu limpieza
-- en algo que el sistema sostiene en el tiempo. Estos son opcionales: activalos
-- recién cuando tu criterio de negocio esté decidido.

ALTER TABLE ventas
    ADD CONSTRAINT ck_ventas_precio_positivo CHECK (precio_unitario > 0);

ALTER TABLE ventas
    ADD CONSTRAINT ck_ventas_fecha_periodo
    CHECK (fecha_venta BETWEEN DATE '2023-01-01' AND DATE '2024-12-31');

ALTER TABLE ventas
    ADD CONSTRAINT ck_ventas_descuento_rango
    CHECK (descuento >= 0 AND descuento <= 1);

-- NO agregues un CHECK de cantidad >= 0 sin pensarlo: si las cantidades
-- negativas son devoluciones legítimas, este constraint te va a bloquear
-- información real del negocio. Esa decisión es tuya y va documentada
-- en el README del proyecto.

-- =============================================================================
-- VERIFICACIÓN FINAL
-- =============================================================================
-- Que las FK existan no alcanza: comprobá que las consultas de negocio
-- devuelvan los mismos totales antes y después de limpiar, y explicá
-- la diferencia en el README. Si el total facturado cambió, tiene que
-- haber una razón escrita.
-- =============================================================================
