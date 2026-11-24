-- Fase 2: registrar si una polar necesitó el reintento de la zona lineal.
ALTER TABLE calculos ADD COLUMN reintento BOOLEAN NOT NULL DEFAULT FALSE;