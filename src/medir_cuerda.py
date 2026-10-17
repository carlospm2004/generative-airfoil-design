# Mide el ángulo de la cuerda de cada perfil (recta del borde de ataque
# al borde de salida) para decidir si hay que derrotarlos al normalizar.

from pathlib import Path

import numpy as np

from lector import leer_perfil

CARPETA_PERFILES = Path("data/raw/coord_seligFmt")

EXCLUIDOS = {
    "naca1.dat",          # carenado de motor, no es un perfil
    "30p-30n.dat",        # multielemento: slat + principal + flap
    "30p-30n-slat.dat",
    "30p-30n-main.dat",
    "30p-30n-flap.dat",
    "r1145msf.dat",
    "r1145msm.dat",
    "ua79sff.dat",
    "ua79sfm.dat",
}

angulos = []   # lista de tuplas (nombre_archivo, angulo_en_grados)

for ruta in sorted(CARPETA_PERFILES.glob("*.dat")):
    if ruta.name in EXCLUIDOS:
        continue

    perfil = leer_perfil(ruta)
    puntos = np.array(perfil["puntos"])

    # Borde de salida: punto medio entre el primer y el último punto
    bs = (puntos[0] + puntos[-1]) / 2

    # Borde de ataque: el punto más alejado del borde de salida
    distancias = np.sqrt(((puntos - bs) ** 2).sum(axis=1))
    ba = puntos[np.argmax(distancias)]

    # Ángulo de la cuerda respecto a la horizontal
    dx, dy = bs - ba
    angulo = np.degrees(np.arctan2(dy, dx))

    angulos.append((ruta.name, angulo))

# Resumen por rangos de |ángulo|
valores = np.abs(np.array([a for _, a in angulos]))

print(f"Perfiles analizados: {len(angulos)}")
print(f"  |ángulo| < 0.1°:      {np.sum(valores < 0.1)}")
print(f"  0.1° <= |ángulo| < 1°: {np.sum((valores >= 0.1) & (valores < 1))}")
print(f"  |ángulo| >= 1°:        {np.sum(valores >= 1)}")

print("\nLos 10 más inclinados:")
for nombre, angulo in sorted(angulos, key=lambda t: abs(t[1]), reverse=True)[:10]:
    print(f"  {nombre:20s} {angulo:+.2f}°")