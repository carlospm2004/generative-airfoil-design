# Piloto de la Fase 2: calcula las polares de una muestra de perfiles a todos los Reynolds
# para medir tiempos, puntos convergidos y fallos antes del cálculo completo.

from pathlib import Path

import numpy as np
import pandas as pd

from xfoil import ALFA_MAX, ALFA_MIN, PASO_ALFA, calcular_polar

RUTA_CATALOGO = Path("data/processed/perfiles.csv")
RUTA_RESUMEN = Path("data/processed/piloto_calculos.csv")
RUTA_POLARES = Path("data/processed/piloto_polares.csv")

N_PERFILES = 50
SEMILLA = 42
REYNOLDS = [5e4, 1e5, 2e5, 5e5, 1e6, 3e6, 6e6, 9e6]
PUNTOS_POSIBLES = int(round((ALFA_MAX - ALFA_MIN) / PASO_ALFA)) + 1   # 51


def resumen_polar(polar):
    """Medidas de calidad de una polar: puntos que faltan, mayor hueco y dónde está el CL máximo."""
    if polar.empty:
        return {"n_puntos": 0, "hueco_max": np.nan, "alfa_cl_max": np.nan, "cl_max_en_limite": False}
    alfas = polar["alpha"].to_numpy()
    return {
        "n_puntos": len(polar),
        "hueco_max": np.diff(alfas).max() if len(alfas) > 1 else np.nan,   # en grados
        "alfa_cl_max": polar.loc[polar["cl"].idxmax(), "alpha"],
        "cl_max_en_limite": polar.loc[polar["cl"].idxmax(), "alpha"] == ALFA_MAX,
    }


if __name__ == "__main__":
    catalogo = pd.read_csv(RUTA_CATALOGO)
    muestra = catalogo.sample(n=N_PERFILES, random_state=SEMILLA)["archivo"].tolist()
    total = len(muestra) * len(REYNOLDS)
    print(f"Piloto: {len(muestra)} perfiles × {len(REYNOLDS)} Reynolds = {total} polares")

    filas = []
    polares = []
    for i, archivo in enumerate(muestra, start=1):
        for reynolds in REYNOLDS:
            estado, polar, segundos = calcular_polar(archivo, reynolds)
            filas.append({"archivo": archivo, "reynolds": reynolds, "estado": estado,
                          "segundos": segundos, **resumen_polar(polar)})
            if not polar.empty:
                polares.append(polar.assign(archivo=archivo, reynolds=reynolds))
        print(f"  {i}/{len(muestra)} {archivo}")

    resumen = pd.DataFrame(filas)
    resumen.to_csv(RUTA_RESUMEN, index=False)
    if polares:
        pd.concat(polares).to_csv(RUTA_POLARES, index=False)

    # --- Resultados ---
    print(f"\nTiempo total: {resumen['segundos'].sum() / 60:.1f} min")
    print("\nTiempo por polar (s), por Reynolds:")
    print(resumen.groupby("reynolds")["segundos"].describe(percentiles=[0.5, 0.95])[["mean", "50%", "95%", "max"]].round(2))

    print("\nEstado de las polares, por Reynolds:")
    print(pd.crosstab(resumen["reynolds"], resumen["estado"], margins=True, margins_name="Total"))

    ok = resumen[resumen["estado"] == "ok"]
    print(f"\nPuntos convergidos (de {PUNTOS_POSIBLES} posibles), en las polares ok:")
    print(ok.groupby("reynolds")["n_puntos"].describe()[["mean", "min", "25%", "50%"]].round(1))

    print("\nPolares con huecos de más de 1 grado, por Reynolds:")
    print((ok["hueco_max"] > 1.0).groupby(ok["reynolds"]).mean().mul(100).round(1).astype(str) + " %")

    print(f"\nPolares con el CL máximo en el límite ({ALFA_MAX:.0f}°), por Reynolds:")
    print(ok.groupby("reynolds")["cl_max_en_limite"].mean().mul(100).round(1).astype(str) + " %")

    print(f"\nGuardado en {RUTA_RESUMEN} y {RUTA_POLARES}")