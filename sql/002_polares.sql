-- Fase 2: resultados de XFOIL.
-- calculos: una fila por perfil y Reynolds, con el resultado del cálculo y su calidad.
-- polares: una fila por punto convergido (perfil, Reynolds, ángulo de ataque).

CREATE TABLE calculos (
    archivo           TEXT NOT NULL REFERENCES perfiles (archivo) ON DELETE CASCADE,
    reynolds          INTEGER NOT NULL,
    estado            TEXT NOT NULL CHECK (estado IN ('ok', 'sin_convergencia', 'tiempo_agotado')),
    segundos          DOUBLE PRECISION NOT NULL,
    n_puntos          INTEGER NOT NULL,
    cobertura_lineal  DOUBLE PRECISION NOT NULL,
    hueco_lineal      DOUBLE PRECISION,
    alfa_cl_max       DOUBLE PRECISION,
    cl_max_en_limite  BOOLEAN NOT NULL,
    valida            BOOLEAN NOT NULL,
    PRIMARY KEY (archivo, reynolds)
);

CREATE TABLE polares (
    archivo       TEXT NOT NULL,
    reynolds      INTEGER NOT NULL,
    alpha         DOUBLE PRECISION NOT NULL,
    cl            DOUBLE PRECISION NOT NULL,
    cd            DOUBLE PRECISION NOT NULL,
    cdp           DOUBLE PRECISION NOT NULL,
    cm            DOUBLE PRECISION NOT NULL,
    top_xtr       DOUBLE PRECISION NOT NULL,
    bot_xtr       DOUBLE PRECISION NOT NULL,
    post_perdida  BOOLEAN NOT NULL,
    PRIMARY KEY (archivo, reynolds, alpha),
    FOREIGN KEY (archivo, reynolds) REFERENCES calculos (archivo, reynolds) ON DELETE CASCADE
);