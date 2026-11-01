# Valida los perfiles limpios de data/processed/perfiles/ y guarda
# una tabla resumen (una fila por perfil) en data/processed/resumen_limpieza.csv

from pathlib import Path

import numpy as np
import pandas as pd

from lector import leer_perfil

CARPETA_PERFILES = Path("data/processed/perfiles")
RUTA_RESUMEN = Path("data/processed/resumen_limpieza.csv")
TOLERANCIA = 1e-5
X_MAX_PERMITIDA = 1.01
MIN_PUNTOS = 20

filas = []

for ruta in sorted(CARPETA_PERFILES.glob("*.dat")):
    puntos = np.array(leer_perfil(ruta)["puntos"])

    # Borde de salida: punto medio entre el primer y el último punto
    bs = (puntos[0] + puntos[-1]) / 2

    # Borde de ataque: distancia del punto más cercano al origen
    # (la limpieza dejó el BA exactamente en (0, 0))
    dist_ba = np.sqrt((puntos ** 2).sum(axis=1)).min()

    # Duplicados: parejas de puntos consecutivos con diferencia (0, 0)
    diferencias = np.diff(puntos, axis=0)
    duplicados = np.sum(np.all(diferencias == 0, axis=1))

    filas.append({
        "archivo": ruta.name,
        "n_puntos": len(puntos),
        "x_min": puntos[:, 0].min(),
        "x_max": puntos[:, 0].max(),
        "dist_ba": dist_ba,
        "bs_x": bs[0],
        "bs_y": bs[1],
        "duplicados": duplicados,
    })

df = pd.DataFrame(filas)

df["valido"] = (
    (df["n_puntos"] >= MIN_PUNTOS)
    & (df["x_min"].abs() < TOLERANCIA)
    & (df["x_max"] <= X_MAX_PERMITIDA)
    & (df["dist_ba"] < TOLERANCIA)
    & ((df["bs_x"] - 1).abs() < TOLERANCIA)
    & (df["bs_y"].abs() < TOLERANCIA)
    & (df["duplicados"] == 0)
)

df.to_csv(RUTA_RESUMEN, index=False)

print(f"Perfiles analizados: {len(df)}")
print(f"Válidos:    {df['valido'].sum()}")
print(f"No válidos: {(~df['valido']).sum()}")

no_validos = df[~df["valido"]]
if not no_validos.empty:
    print("\nPerfiles no válidos:")
    print(no_validos)

print("\nEstadísticas:")
print(df[["n_puntos", "x_min", "x_max"]].describe())

print(f"\nResumen guardado en {RUTA_RESUMEN}")