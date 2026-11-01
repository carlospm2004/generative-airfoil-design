# Limpieza de perfiles: exclusiones, duplicados y normalización.
# Decisiones justificadas en docs/formato_dat.md

from pathlib import Path

import numpy as np

from lector import leer_perfil

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


def quitar_duplicados(puntos):
    """Elimina los puntos consecutivos idénticos."""
    sin_duplicados = [puntos[0]]

    for punto in puntos[1:]:
        if not np.array_equal(punto, sin_duplicados[-1]):
            sin_duplicados.append(punto)

    return np.array(sin_duplicados)


def normalizar(puntos):
    """Traslada, gira y escala: BA en (0, 0) y BS en (1, 0)."""
    # Borde de salida: punto medio entre el primer y el último punto
    bs = (puntos[0] + puntos[-1]) / 2

    # Borde de ataque: el punto más alejado del borde de salida
    distancias = np.sqrt(((puntos - bs) ** 2).sum(axis=1))
    ba = puntos[np.argmax(distancias)]

    # Trasladar: el borde de ataque pasa al origen
    puntos = puntos - ba
    dx, dy = bs - ba

    # Girar: la cuerda queda sobre el eje x
    theta = np.arctan2(dy, dx)
    x = puntos[:, 0]
    y = puntos[:, 1]
    x_girada = x * np.cos(theta) + y * np.sin(theta)
    y_girada = -x * np.sin(theta) + y * np.cos(theta)
    puntos = np.column_stack((x_girada, y_girada))

    # Escalar: la cuerda pasa a medir 1
    cuerda = np.sqrt(dx**2 + dy**2)
    return puntos / cuerda


def limpiar_perfil(ruta):
    """Lee y limpia un perfil. Devuelve None si está excluido."""
    if Path(ruta).name in EXCLUIDOS:
        return None

    perfil = leer_perfil(ruta)
    puntos = np.array(perfil["puntos"])
    puntos = quitar_duplicados(puntos)
    puntos = normalizar(puntos)

    return {"nombre": perfil["nombre"], "puntos": puntos}


if __name__ == "__main__":
    perfil = limpiar_perfil("data/raw/coord_seligFmt/ag35.dat")
    print(perfil["nombre"])
    print(perfil["puntos"][:3])