# Carga el catálogo de perfiles y sus coordenadas en la base de datos PostgreSQL.
# Requiere la base levantada (docker compose up -d) y los datos generados en data/processed/.

import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

RUTA_CATALOGO = Path("data/processed/perfiles.csv")
CARPETA_PERFILES = Path("data/processed/perfiles")

COLUMNAS_PERFILES = [
    "archivo", "nombre", "familia", "descripcion",
    "t_max", "x_t_max", "f_max", "x_f_max", "f_min",
    "espesor_bs", "area", "simetrico",
]

load_dotenv()


def conectar():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def filas_perfiles(catalogo):
    """Convierte el catálogo en tuplas con tipos de Python y None en lugar de NaN."""
    df = catalogo[COLUMNAS_PERFILES]
    return list(df.astype(object).where(df.notna(), None).itertuples(index=False, name=None))


def filas_coordenadas(archivos):
    """Devuelve una tupla (archivo, orden, x, y) por cada punto de cada perfil."""
    filas = []
    for archivo in archivos:
        puntos = np.loadtxt(CARPETA_PERFILES / archivo, skiprows=1)
        for orden, (x, y) in enumerate(puntos):
            filas.append((archivo, orden, float(x), float(y)))
    return filas


if __name__ == "__main__":
    catalogo = pd.read_csv(RUTA_CATALOGO)
    perfiles = filas_perfiles(catalogo)
    coordenadas = filas_coordenadas(catalogo["archivo"])
    print(f"Leídos: {len(perfiles)} perfiles y {len(coordenadas)} puntos")

    with conectar() as conn:
        with conn.cursor() as cur:
            # Vaciar antes de cargar: el script se puede ejecutar varias veces
            cur.execute("TRUNCATE perfiles CASCADE")

            # Primero perfiles: la clave foránea de coordenadas apunta a ellos
            execute_values(
                cur,
                f"INSERT INTO perfiles ({', '.join(COLUMNAS_PERFILES)}) VALUES %s",
                perfiles,
            )
            execute_values(
                cur,
                "INSERT INTO coordenadas (archivo, orden, x, y) VALUES %s",
                coordenadas,
                page_size=10_000,
            )

            # Validación: lo que hay en la base frente a lo que se ha leído
            cur.execute("SELECT COUNT(*) FROM perfiles")
            n_perfiles = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM coordenadas")
            n_puntos = cur.fetchone()[0]
            print(f"En la base: {n_perfiles} perfiles y {n_puntos} puntos")

            cur.execute("SELECT familia, COUNT(*) FROM perfiles GROUP BY familia")
            familias_bd = dict(cur.fetchall())
            familias_csv = catalogo["familia"].value_counts().to_dict()

    assert n_perfiles == len(perfiles), "No coincide el número de perfiles"
    assert n_puntos == len(coordenadas), "No coincide el número de puntos"
    assert familias_bd == familias_csv, "No coinciden los recuentos por familia"
    print("Validación correcta: perfiles, puntos y familias coinciden con los datos")