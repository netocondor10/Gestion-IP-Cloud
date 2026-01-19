-- Ejecutar esto en PostgreSQL para QA
CREATE TABLE IF NOT EXISTS registro_auditoria (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(50),
    accion TEXT
);