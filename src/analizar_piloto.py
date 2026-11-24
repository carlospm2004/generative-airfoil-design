# Análisis de los resultados del piloto de XFOIL, para decidir el tiempo máximo
# y los criterios de calidad de las polares.

from pathlib import Path

import pandas as pd

RUTA_RESUMEN = Path("data/processed/piloto_calculos.csv")
RUTA_POLARES = Path("data/processed/piloto_polares.csv")

TRAMOS_ALFA = [-5.0, -2.0, 10.0, 15.0, 20.0]   # negativos, zona lineal, cerca de la pérdida, tras la pérdida
COBERTURAS = [0.7, 0.8, 0.9]                    # criterios candidatos de cobertura de la zona lineal
HUECOS = [1.0, 1.5, 2.0]                        # criterios candidatos de hueco máximo en la zona lineal (grados)

if __name__ == "__main__":
    resumen = pd.read_csv(RUTA_RESUMEN)
    polares = pd.read_csv(RUTA_POLARES)
    con_puntos = resumen[resumen["n_puntos"] > 0]

    # 1. Tiempos y estados
    print(f"1. Tiempo total: {resumen['segundos'].sum() / 60:.1f} min")
    print("   Tiempo de las polares terminadas (s):")
    print(resumen.loc[resumen["estado"] == "ok", "segundos"].describe(percentiles=[0.5, 0.95, 0.99]).round(1).to_string())
    print("\n   Estado de las polares, por Reynolds:")
    print(pd.crosstab(resumen["reynolds"], resumen["estado"], margins=True, margins_name="Total").to_string())

    # 2. Recuperación de las polares que agotan el tiempo
    agotadas = resumen[resumen["estado"] == "tiempo_agotado"]
    print(f"\n2. Polares con tiempo agotado: {len(agotadas)}")
    print(f"   Con puntos recuperados: {(agotadas['n_puntos'] > 0).sum()} "
          f"(media de {agotadas.loc[agotadas['n_puntos'] > 0, 'n_puntos'].mean():.1f} puntos)")

    # 3. Perfiles que fallan a casi todos los Reynolds
    sin_datos = resumen[resumen["n_puntos"] == 0].groupby("archivo").size().sort_values(ascending=False)
    print("\n3. Perfiles con polares sin ningún punto:")
    print(sin_datos.to_string() if len(sin_datos) else "   Ninguno")

    # 4. Cobertura de la zona lineal
    print("\n4. Cobertura de la zona lineal, polares con algún punto:")
    print(pd.cut(con_puntos["cobertura_lineal"], [-0.01, 0.5, 0.7, 0.8, 0.9, 1.0]).value_counts().sort_index().to_string())

    # 5. Criterios candidatos: % de TODAS las polares que serían válidas
    print("\n5. Polares válidas (% del total) según el criterio: cobertura >= fila y hueco <= columna (grados)")
    tabla = pd.DataFrame(
        {h: [((resumen["cobertura_lineal"] >= c) & (resumen["hueco_lineal"] <= h)).mean() * 100 for c in COBERTURAS] for h in HUECOS},
        index=COBERTURAS,
    ).round(1)
    print(tabla.to_string())

    print("\n   Por Reynolds, con cobertura >= 0,8:")
    por_re = pd.DataFrame({
        f"hueco <= {h}": ((resumen["cobertura_lineal"] >= 0.8) & (resumen["hueco_lineal"] <= h)).groupby(resumen["reynolds"]).mean() * 100
        for h in HUECOS
    }).round(1)
    print(por_re.to_string())

    # 6. Puntos después de la pérdida y CD alto
    altos = polares[polares["cd"] > 0.2]
    print(f"\n6. Puntos con CD > 0,2: {len(altos)}, de ellos después del CL máximo: {altos['post_perdida'].mean():.1%}")
    altos_pre = altos[~altos["post_perdida"]].copy()
    if len(altos_pre):
        altos_pre["tramo"] = pd.cut(altos_pre["alpha"], TRAMOS_ALFA, include_lowest=True)
        print("   Los que están antes del CL máximo, por Reynolds y tramo:")
        print(altos_pre.groupby(["reynolds", "tramo"], observed=False).size().unstack().to_string())
    print(f"   Puntos después de la pérdida: {polares['post_perdida'].mean():.1%} del total")

    # 7. CL máximo en el límite
    print("\n7. Polares con el CL máximo en el último ángulo (20°), por Reynolds:")
    print((con_puntos.groupby("reynolds")["cl_max_en_limite"].mean() * 100).round(1).astype(str).add(" %").to_string())