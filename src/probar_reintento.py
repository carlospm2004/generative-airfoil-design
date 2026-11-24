# Experimento: ¿un segundo barrido de la zona lineal, con paso más fino, recupera las polares no válidas?
# Se repite sobre las polares no válidas del piloto y se mide cuántas pasan a ser válidas y cuánto cuesta.

from pathlib import Path

import pandas as pd

from polares import calidad_polar
from xfoil import ALFA_MAX, BARRIDOS_REINTENTO, calcular_polar, combinar_polares

RUTA_RESUMEN = Path("data/processed/piloto_calculos.csv")
RUTA_POLARES = Path("data/processed/piloto_polares.csv")

if __name__ == "__main__":
    resumen = pd.read_csv(RUTA_RESUMEN)
    polares = pd.read_csv(RUTA_POLARES)

    resumen["valida"] = [calidad_polar(polares[(polares["archivo"] == f.archivo) & (polares["reynolds"] == f.reynolds)]
                                       .drop(columns=["archivo", "reynolds"]).reset_index(drop=True), ALFA_MAX)["valida"]
                         for f in resumen.itertuples()]
    candidatas = resumen[~resumen["valida"] & (resumen["n_puntos"] > 0)]
    print(f"Polares del piloto: {len(resumen)} | válidas: {resumen['valida'].sum()} ({resumen['valida'].mean():.1%})")
    print(f"No válidas con algún punto (se reintentan): {len(candidatas)}\n")

    filas = []
    for i, f in enumerate(candidatas.itertuples(), start=1):
        original = (polares[(polares["archivo"] == f.archivo) & (polares["reynolds"] == f.reynolds)]
                    .drop(columns=["archivo", "reynolds", "post_perdida"]).reset_index(drop=True))
        estado, reintento, segundos = calcular_polar(f.archivo, f.reynolds, barridos=BARRIDOS_REINTENTO)
        combinada = combinar_polares(original, reintento)
        calidad = calidad_polar(combinada, ALFA_MAX)
        filas.append({"archivo": f.archivo, "reynolds": f.reynolds, "estado_reintento": estado, "segundos": segundos,
                      "cobertura_antes": f.cobertura_lineal, "cobertura_despues": calidad["cobertura_lineal"],
                      "valida_despues": calidad["valida"]})
        print(f"  {i}/{len(candidatas)} {f.archivo} Re={f.reynolds:.0e}: "
              f"cobertura {f.cobertura_lineal:.2f} -> {calidad['cobertura_lineal']:.2f} "
              f"{'VÁLIDA' if calidad['valida'] else ''}")

    r = pd.DataFrame(filas)
    print(f"\nRecuperadas: {r['valida_despues'].sum()} de {len(r)} ({r['valida_despues'].mean():.1%})")
    print(f"Tiempo del reintento: media {r['segundos'].mean():.1f} s, total {r['segundos'].sum() / 60:.1f} min")
    validas = resumen["valida"].sum() + r["valida_despues"].sum()
    print(f"Polares válidas del piloto: {resumen['valida'].mean():.1%} -> {validas / len(resumen):.1%}")
    print("\nRecuperadas por Reynolds (% de las reintentadas):")
    print((r.groupby("reynolds")["valida_despues"].mean() * 100).round(1).to_string())