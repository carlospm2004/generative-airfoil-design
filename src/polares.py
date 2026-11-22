# Características aerodinámicas que se extraen de una polar.

import numpy as np

RANGO_LINEAL = (-2.0, 6.0)   # grados; zona lineal de CL(alpha) en perfiles de uso general


def caracteristicas_polar(polar):
    """Devuelve las características principales de una polar (DataFrame de xfoil.calcular_polar)."""
    lineal = polar[polar["alpha"].between(*RANGO_LINEAL)]
    pendiente, ordenada = np.polyfit(lineal["alpha"], lineal["cl"], 1)
    i_cd = polar["cd"].idxmin()
    i_cl = polar["cl"].idxmax()
    return {
        "pendiente": pendiente,                          # dCL/dalpha, en 1/grado
        "alfa_l0": -ordenada / pendiente,                # ángulo de sustentación nula, en grados
        "cm0": np.interp(0.0, polar["alpha"], polar["cm"]),
        "cd_min": polar.loc[i_cd, "cd"],
        "cl_cd_min": polar.loc[i_cd, "cl"],              # CL al que se da el CD mínimo
        "cl_max": polar.loc[i_cl, "cl"],
        "alfa_cl_max": polar.loc[i_cl, "alpha"],
        "cl_max_en_limite": polar.loc[i_cl, "alpha"] == polar["alpha"].max(),
    }