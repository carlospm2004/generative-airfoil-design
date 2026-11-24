# ¿Cuánto error se comete al interpolar un hueco de la zona lineal?
# Se toman las polares completas del piloto, se quitan puntos a propósito y se comparan
# los valores interpolados con los calculados por XFOIL.

from pathlib import Path

import numpy as np
import pandas as pd

RUTA_POLARES = Path("data/processed/piloto_polares.csv")

ZONA_LINEAL = (-2.0, 10.0)
PASO_ALFA = 0.5
HUECOS = [1.0, 1.5, 2.0, 2.5]          # grados entre los dos puntos que quedan a cada lado
GRUPOS_RE = {"Re <= 2e5": (0, 2e5), "Re >= 5e5": (5e5, 1e8)}


def errores_hueco(polar, hueco):
    """Quita los puntos de un hueco en cada posición posible y devuelve los errores de interpolar."""
    alfas = polar["alpha"].to_numpy()
    errores = []
    for inicio in np.arange(ZONA_LINEAL[0], ZONA_LINEAL[1] - hueco + 1e-9, PASO_ALFA):
        fin = inicio + hueco
        quitados = (alfas > inicio + 1e-9) & (alfas < fin - 1e-9)
        quedan = ~quitados
        for columna in ["cl", "cd", "cm"]:
            interpolado = np.interp(alfas[quitados], alfas[quedan], polar[columna].to_numpy()[quedan])
            real = polar[columna].to_numpy()[quitados]
            error = np.abs(interpolado - real)
            if columna == "cd":
                error = error / real          # error relativo
            errores += [(columna, e) for e in error]
    return errores


if __name__ == "__main__":
    polares = pd.read_csv(RUTA_POLARES)
    a, b = ZONA_LINEAL
    n_posibles = int(round((b - a) / PASO_ALFA)) + 1       # incluye los dos extremos: 25

    filas = []
    n_completas = 0
    for (archivo, reynolds), polar in polares.groupby(["archivo", "reynolds"]):
        zona = polar[polar["alpha"].between(a, b)].sort_values("alpha")
        if len(zona) < n_posibles:
            continue                                        # solo polares con la zona lineal completa
        n_completas += 1
        for hueco in HUECOS:
            for columna, error in errores_hueco(zona, hueco):
                filas.append({"reynolds": reynolds, "hueco": hueco, "magnitud": columna, "error": error})

    errores = pd.DataFrame(filas)
    print(f"Polares con la zona lineal completa usadas: {n_completas}")

    for grupo, (re_min, re_max) in GRUPOS_RE.items():
        datos = errores[errores["reynolds"].between(re_min, re_max)]
        tabla = datos.groupby(["hueco", "magnitud"])["error"].quantile([0.5, 0.95]).unstack().unstack("magnitud")
        tabla.columns = [f"{magnitud} p{int(q * 100)}" for q, magnitud in tabla.columns]
        tabla = tabla[["cl p50", "cl p95", "cd p50", "cd p95", "cm p50", "cm p95"]]
        print(f"\n{grupo} — error de interpolación (CL y CM absolutos, CD relativo):")
        print(tabla.round({"cl p50": 4, "cl p95": 4, "cm p50": 4, "cm p95": 4, "cd p50": 3, "cd p95": 3}).to_string())