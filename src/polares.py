# Características y calidad de una polar.

import numpy as np

RANGO_LINEAL = (-2.0, 6.0)        # grados; ajuste de la pendiente en perfiles de uso general
ZONA_LINEAL = (-2.0, 10.0)        # grados; zona antes de la pérdida que debe estar bien cubierta
PASO_ALFA = 0.5


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


def calidad_polar(polar, alfa_max):
    """Medidas de calidad de una polar, para decidir si es válida.

    - n_puntos: puntos convergidos.
    - cobertura_lineal: fracción de los puntos posibles de la zona lineal que han convergido.
    - hueco_lineal: mayor salto entre dos ángulos convergidos dentro de la zona lineal (grados).
    - alfa_cl_max, cl_max_en_limite: dónde está el CL máximo y si coincide con el último ángulo posible.
    """
    a, b = ZONA_LINEAL
    posibles = int(round((b - a) / PASO_ALFA))          # ángulos en (a, b]: 24
    if polar.empty:
        return {"n_puntos": 0, "cobertura_lineal": 0.0, "hueco_lineal": np.nan,
                "alfa_cl_max": np.nan, "cl_max_en_limite": False}
    alfas = polar.loc[(polar["alpha"] > a) & (polar["alpha"] <= b), "alpha"].sort_values().to_numpy()
    # El hueco se mide incluyendo los extremos de la zona: si falta el principio o el final, también cuenta
    bordes = np.concatenate([[a], alfas, [b]]) if len(alfas) else np.array([a, b])
    alfa_cl_max = polar.loc[polar["cl"].idxmax(), "alpha"]
    return {
        "n_puntos": len(polar),
        "cobertura_lineal": len(alfas) / posibles,
        "hueco_lineal": np.diff(bordes).max(),
        "alfa_cl_max": alfa_cl_max,
        "cl_max_en_limite": alfa_cl_max == alfa_max,
    }


def marcar_post_perdida(polar):
    """Añade la columna post_perdida: True en los puntos con alfa mayor que el del CL máximo."""
    if polar.empty:
        return polar.assign(post_perdida=False)
    alfa_cl_max = polar.loc[polar["cl"].idxmax(), "alpha"]
    return polar.assign(post_perdida=polar["alpha"] > alfa_cl_max)