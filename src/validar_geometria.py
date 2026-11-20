# Valida la geometría con los NACA de 4 cifras, cuyo nombre codifica su forma:
# NACA MPXX -> curvatura máxima M %, en la posición P/10 de la cuerda, espesor XX %.

from pathlib import Path

import numpy as np
import pandas as pd

RUTA_GEOMETRIA = Path("data/processed/geometria.csv")

TOLERANCIA_T = 0.002    # 0,2 % de cuerda
TOLERANCIA_F = 0.002    # 0,2 % de cuerda
TOLERANCIA_XF = 0.02    # 2 % de cuerda

# Archivos que no cumplen por un problema de los datos, no del cálculo
EXCEPCIONES = {
    "naca2411.dat": "la cabecera dice NACA 2.5411: curvatura del 2,5 %, no del 2 %",
    "naca1410.dat": "coordenadas con línea media casi plana entre 0,3c y 0,5c; "
                    "el máximo cae en 0,5c en lugar de 0,4c",
}


def cifras_naca4(archivo):
    """Devuelve las 4 cifras si el archivo es un NACA de 4 cifras, o None."""
    nombre = archivo.removesuffix(".dat")

    for prefijo in ("naca", "n"):
        if nombre.startswith(prefijo):
            cifras = nombre[len(prefijo):]
            if len(cifras) == 4 and cifras.isdigit():
                return cifras

    return None


df = pd.read_csv(RUTA_GEOMETRIA)

# Seleccionar los NACA de 4 cifras
df["cifras"] = df["archivo"].apply(cifras_naca4)
naca = df[df["cifras"].notna()].copy()

# Valores teóricos a partir del nombre
naca["f_teorica"] = naca["cifras"].str[0].astype(int) / 100
naca["x_f_teorica"] = naca["cifras"].str[1].astype(int) / 10
naca["t_teorico"] = naca["cifras"].str[2:].astype(int) / 100

# En los simétricos (M = 0) no hay posición de curvatura
naca.loc[naca["f_teorica"] == 0, "x_f_teorica"] = np.nan

# Errores
naca["error_t"] = (naca["t_max"] - naca["t_teorico"]).abs()
naca["error_f"] = (naca["f_max"] - naca["f_teorica"]).abs()
naca["error_xf"] = (naca["x_f_max"] - naca["x_f_teorica"]).abs()

naca["valido"] = (
    (naca["error_t"] <= TOLERANCIA_T)
    & (naca["error_f"] <= TOLERANCIA_F)
    & ((naca["error_xf"] <= TOLERANCIA_XF) | naca["x_f_teorica"].isna())
)

naca["excepcion"] = naca["archivo"].isin(EXCEPCIONES.keys())

columnas = ["archivo", "t_teorico", "t_max", "f_teorica", "f_max",
            "x_f_teorica", "x_f_max", "valido"]

print(f"NACA de 4 cifras encontrados: {len(naca)}")
print(f"Válidos:    {naca['valido'].sum()}")
print(f"No válidos: {(~naca['valido']).sum()}")
print()
print(naca[columnas].round(4).to_string(index=False))

# Fallos que no están explicados como excepción: estos sí indicarían un problema
inesperados = naca[~naca["valido"] & ~naca["excepcion"]]

print("\nExcepciones conocidas:")
for archivo, motivo in EXCEPCIONES.items():
    print(f"  {archivo}: {motivo}")

print(f"\nFallos inesperados: {len(inesperados)}")
if not inesperados.empty:
    print(inesperados[columnas].round(4).to_string(index=False))

# Errores máximos sin contar las excepciones
normales = naca[~naca["excepcion"]]
print(f"\nError máximo en t:   {normales['error_t'].max():.4f}")
print(f"Error máximo en f:   {normales['error_f'].max():.4f}")
print(f"Error máximo en x_f: {normales['error_xf'].max():.4f}")