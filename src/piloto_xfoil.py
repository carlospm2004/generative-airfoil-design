# Piloto de la Fase 2: calcula las polares de una muestra de perfiles a todos los Reynolds
# para medir tiempos, puntos convergidos y fallos antes del cálculo completo.

from pathlib import Path

import pandas as pd

from polares import calidad_polar, marcar_post_perdida
from xfoil import ALFA_MAX, REYNOLDS, calcular_polar

RUTA_CATALOGO = Path("data/processed/perfiles.csv")
RUTA_RESUMEN = Path("data/processed/piloto_calculos.csv")
RUTA_POLARES = Path("data/processed/piloto_polares.csv")

N_PERFILES = 50
SEMILLA = 42

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
                          "segundos": segundos, **calidad_polar(polar, ALFA_MAX)})
            if not polar.empty:
                polares.append(marcar_post_perdida(polar).assign(archivo=archivo, reynolds=reynolds))
        print(f"  {i}/{len(muestra)} {archivo}")

    resumen = pd.DataFrame(filas)
    resumen.to_csv(RUTA_RESUMEN, index=False)
    if polares:
        pd.concat(polares).to_csv(RUTA_POLARES, index=False)

    print(f"\nTiempo total: {resumen['segundos'].sum() / 60:.1f} min")
    print("\nEstado de las polares, por Reynolds:")
    print(pd.crosstab(resumen["reynolds"], resumen["estado"], margins=True, margins_name="Total"))
    print(f"\nGuardado en {RUTA_RESUMEN} y {RUTA_POLARES}")
    print("Análisis detallado: python src/analizar_piloto.py")