-- Esquema de la base de datos de Airfoil AI.
-- PostgreSQL lo ejecuta automáticamente al crear el volumen por primera vez.

CREATE TABLE perfiles (
    archivo      TEXT PRIMARY KEY,
    nombre       TEXT NOT NULL,
    familia      TEXT NOT NULL,
    descripcion  TEXT,
    t_max        DOUBLE PRECISION NOT NULL,
    x_t_max      DOUBLE PRECISION NOT NULL,
    f_max        DOUBLE PRECISION NOT NULL,
    x_f_max      DOUBLE PRECISION,
    f_min        DOUBLE PRECISION NOT NULL,
    espesor_bs   DOUBLE PRECISION NOT NULL,
    area         DOUBLE PRECISION NOT NULL,
    simetrico    BOOLEAN NOT NULL
);

CREATE TABLE coordenadas (
    archivo  TEXT NOT NULL REFERENCES perfiles (archivo) ON DELETE CASCADE,
    orden    INTEGER NOT NULL,
    x        DOUBLE PRECISION NOT NULL,
    y        DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (archivo, orden)
);