# Limpia todos los perfiles de data/raw y los guarda en data/processed/perfiles/
# en formato Selig (.dat): nombre en la primera línea y pares x y debajo.

from pathlib import Path

import numpy as np

from limpieza import limpiar_perfil

CARPETA_ENTRADA = Path("data/raw/coord_seligFmt")
CARPETA_SALIDA = Path("data/processed/perfiles")

CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

guardados = 0
excluidos = 0

for ruta in sorted(CARPETA_ENTRADA.glob("*.dat")):
    perfil = limpiar_perfil(ruta)

    if perfil is None:
        excluidos += 1
        continue

    np.savetxt(
        CARPETA_SALIDA / ruta.name,
        perfil["puntos"],
        fmt="%.6f",
        header=perfil["nombre"],
        comments="",
    )
    guardados += 1

print(f"Guardados: {guardados}")
print(f"Excluidos: {excluidos}")