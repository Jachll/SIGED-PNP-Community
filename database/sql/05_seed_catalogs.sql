-- archivo: database/sql/05_seed_catalogs.sql
\connect siged_pnp;

INSERT INTO delitos (id_delito, nombre_delito, descripcion) VALUES
    (1, 'Robo agravado', 'Sustraccion con violencia o amenaza'),
    (2, 'Hurto', 'Sustraccion sin violencia'),
    (3, 'Violencia familiar', 'Agresion fisica o psicologica en el hogar'),
    (4, 'Microcomercializacion de drogas', 'Venta o distribucion en pequena escala'),
    (5, 'Lesiones', 'Danos a la integridad fisica'),
    (6, 'Extorsion', 'Amenazas para obtener beneficio economico')
ON CONFLICT (id_delito) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('delitos', 'id_delito'),
    (SELECT GREATEST(COALESCE(MAX(id_delito), 1), 1) FROM delitos),
    true
);

INSERT INTO comisarias (id_comisaria, nombre_comisaria, distrito, direccion) VALUES
    (1, 'Comisaria Demo Norte', 'DISTRITO DEMO NORTE', 'Av. Sintetica 100'),
    (2, 'Comisaria Demo Centro', 'DISTRITO DEMO CENTRO', 'Jr. Ejemplo 200'),
    (3, 'Comisaria Demo Sur', 'DISTRITO DEMO SUR', 'Calle Prueba 300'),
    (4, 'Comisaria Demo Este', 'DISTRITO DEMO ESTE', 'Av. Muestra 400'),
    (5, 'Comisaria Demo Oeste', 'DISTRITO DEMO OESTE', 'Jr. Demostracion 500'),
    (6, 'Comisaria Demo Rural', 'DISTRITO DEMO RURAL', 'Camino Local 600')
ON CONFLICT (id_comisaria) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('comisarias', 'id_comisaria'),
    (SELECT GREATEST(COALESCE(MAX(id_comisaria), 1), 1) FROM comisarias),
    true
);
