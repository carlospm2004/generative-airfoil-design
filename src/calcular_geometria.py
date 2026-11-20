# Calcula las características geométricas de los perfiles limpios
# y las guarda en data/processed/geometria.csv (una fila por perfil).

from pathlib import Path

import numpy as np
import pandas as pd

from geometria import caracteristicas
from lector import leer_perfil

CARPETA_PERFILES = Path("data/processed/perfiles")
RUTA_SALIDA = Path("data/processed/geometria.csv")
UMBRAL_CURVATURA = 1e-4   # por debajo, la curvatura se considera nula

filas = []

for ruta in sorted(CARPETA_PERFILES.glob("*.dat")):
    perfil = leer_perfil(ruta)
    puntos = np.array(perfil["puntos"])

    filas.append({
        "archivo": ruta.name,
        "nombre": perfil["nombre"],
        **caracteristicas(puntos),
    })

df = pd.DataFrame(filas)

# Simétrico: la línea media no se separa de la cuerda ni hacia arriba ni hacia abajo
df["simetrico"] = (
    (df["f_max"] < UMBRAL_CURVATURA)
    & (df["f_min"] > -UMBRAL_CURVATURA)
)

# Sin curvatura positiva, la posición de la curvatura máxima no tiene sentido físico
df.loc[df["f_max"] < UMBRAL_CURVATURA, "x_f_max"] = np.nan

df = df.round(6)
df.to_csv(RUTA_SALIDA, index=False)

print(f"Perfiles: {len(df)}")
print(f"Simétricos: {df['simetrico'].sum()}")
print(f"Sin posición de curvatura (x_f_max vacío): {df['x_f_max'].isna().sum()}")
print("\nEstadísticas:")
print(df.describe().round(4).to_string())
print(f"\nTabla guardada en {RUTA_SALIDA}")