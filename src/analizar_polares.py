# Análisis del dataset de polares (Fase 2): comprobación física de los resultados de XFOIL
# y figuras para la documentación.
#
# Uso: python src/analizar_polares.py   (con la base de datos levantada)
# Las figuras se guardan en docs/figuras/.

from pathlib import Path

import matplotlib

matplotlib.use("Agg")                     # genera imágenes sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cargar_bd import conectar
from polares import caracteristicas_polar

CARPETA_FIGURAS = Path("docs/figuras")
RE_REFERENCIA = 3_000_000                 # Reynolds para la comparación con la teoría

# Colores (paleta validada para daltonismo) y tipografía de las figuras
COLOR_DATOS = "#257de0"
COLOR_TEORIA = "#f47230"
COLOR_TEXTO = "#191919"
COLOR_SECUNDARIO = "#666666"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": COLOR_SECUNDARIO, "axes.labelcolor": COLOR_TEXTO,
    "xtick.color": COLOR_SECUNDARIO, "ytick.color": COLOR_SECUNDARIO, "axes.grid": True,
    "grid.color": "#e5e5e5", "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
})


def leer(sql):
    """Ejecuta una consulta y devuelve un DataFrame."""
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(sql)
        columnas = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columnas)


def caracteristicas(polar):
    """Características de una polar válida, más la eficiencia máxima antes de la pérdida."""
    c = caracteristicas_polar(polar.reset_index(drop=True))
    antes = polar[~polar["post_perdida"] & (polar["cd"] > 0)]
    eficiencia = antes["cl"] / antes["cd"]
    c["ld_max"] = eficiencia.max()
    c["cl_ld_max"] = antes.loc[eficiencia.idxmax(), "cl"]
    return pd.Series(c)


def figura_reynolds(resumen, ruta):
    """Cuatro paneles: mediana y rango intercuartílico de cada magnitud frente al Reynolds."""
    paneles = [
        ("cd_min", "CD mínimo"),
        ("cl_max", "CL máximo"),
        ("ld_max", "Eficiencia máxima (L/D)"),
        ("pendiente", "Pendiente dCL/dα (1/°)"),
    ]
    fig, ejes = plt.subplots(2, 2, figsize=(9, 6.5), sharex=True)
    for eje, (columna, titulo) in zip(ejes.flat, paneles):
        datos = resumen[columna]
        eje.fill_between(datos.index, datos["p25"], datos["p75"], color=COLOR_DATOS, alpha=0.18, linewidth=0,
                         label="Percentiles 25–75")
        eje.plot(datos.index, datos["p50"], color=COLOR_DATOS, linewidth=2, marker="o", markersize=5, label="Mediana")
        eje.set_title(titulo, loc="left", color=COLOR_TEXTO, fontsize=11)
        eje.set_xscale("log")
    ejes[1, 1].axhline(2 * np.pi * np.pi / 180, color=COLOR_TEORIA, linewidth=2, linestyle="--",
                       label="Teoría (2π/rad)")
    for eje in ejes[1]:
        eje.set_xlabel("Número de Reynolds")
    ejes[0, 0].legend(frameon=False, loc="upper right")
    ejes[1, 1].legend(frameon=False, loc="lower right")
    fig.suptitle("Características de las polares válidas según el Reynolds", x=0.02, ha="left",
                 fontsize=13, color=COLOR_TEXTO)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def figura_teoria(datos, ruta):
    """Ángulo de sustentación nula y CM frente a la curvatura máxima, con la teoría del perfil delgado."""
    f = np.linspace(0, datos["f_max"].max(), 50)
    fig, (eje1, eje2) = plt.subplots(1, 2, figsize=(9, 3.8))
    eje1.scatter(datos["f_max"] * 100, datos["alfa_l0"], s=10, color=COLOR_DATOS, alpha=0.5, linewidths=0, label="XFOIL")
    eje1.plot(f * 100, np.degrees(-2 * f), color=COLOR_TEORIA, linewidth=2, label="Teoría: α_L0 = −2f")
    eje1.set_xlabel("Curvatura máxima (% de la cuerda)")
    eje1.set_title("Ángulo de sustentación nula (°)", loc="left", color=COLOR_TEXTO, fontsize=11)
    eje2.scatter(datos["f_max"] * 100, datos["cm0"], s=10, color=COLOR_DATOS, alpha=0.5, linewidths=0, label="XFOIL")
    eje2.plot(f * 100, -np.pi * f, color=COLOR_TEORIA, linewidth=2, label="Teoría: CM = −πf")
    eje2.set_xlabel("Curvatura máxima (% de la cuerda)")
    eje2.set_title("Coeficiente de momento a α = 0°", loc="left", color=COLOR_TEXTO, fontsize=11)
    for eje in (eje1, eje2):
        eje.legend(frameon=False, loc="lower left")
    fig.suptitle(f"Comparación con la teoría del perfil delgado (Re = {RE_REFERENCIA / 1e6:.0f}·10⁶)", x=0.02, ha="left",
                 fontsize=13, color=COLOR_TEXTO)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    CARPETA_FIGURAS.mkdir(parents=True, exist_ok=True)

    perfiles = leer("SELECT archivo, familia, t_max, f_max, simetrico FROM perfiles")
    calculos = leer("SELECT * FROM calculos")
    polares = leer("""
        SELECT p.* FROM polares p
        JOIN calculos c USING (archivo, reynolds)
        WHERE c.valida
        ORDER BY p.archivo, p.reynolds, p.alpha
    """)

    # 1. Resumen general
    print("1. Resumen general")
    print(f"   Cálculos: {len(calculos)} | válidos: {calculos['valida'].sum()} ({calculos['valida'].mean():.1%})")
    print(f"   Reintentados: {calculos['reintento'].sum()} ({calculos['reintento'].mean():.1%}), "
          f"de los que acabaron válidos: {calculos.loc[calculos['reintento'], 'valida'].mean():.1%}")
    print(f"   Tiempo de XFOIL: {calculos['segundos'].sum() / 3600:.1f} h")
    print(f"   Puntos en las polares válidas: {len(polares)}")

    # 2. Perfiles sin ninguna polar válida: ¿tienen algo en común?
    validas_perfil = calculos.groupby("archivo")["valida"].sum()
    fallidos = perfiles[perfiles["archivo"].isin(validas_perfil[validas_perfil == 0].index)]
    print(f"\n2. Perfiles sin ninguna polar válida: {len(fallidos)}")
    comparacion = pd.DataFrame({
        "fallidos": fallidos[["t_max", "f_max"]].median() * 100,
        "todos": perfiles[["t_max", "f_max"]].median() * 100,
    }).rename(index={"t_max": "espesor (%)", "f_max": "curvatura (%)"}).round(1)
    print("   Medianas de geometría:")
    print(comparacion.to_string())
    print("   Por familia:")
    print(fallidos["familia"].value_counts().to_string())
    print("   Perfiles:", ", ".join(sorted(fallidos["archivo"])))

    # 3. Validez según la geometría
    con_geometria = calculos.merge(perfiles, on="archivo")
    con_geometria["espesor"] = pd.cut(con_geometria["t_max"] * 100, [0, 6, 9, 12, 15, 18, 100])
    print("\n3. Polares válidas (%) según el espesor máximo (% de la cuerda):")
    print((con_geometria.groupby("espesor", observed=True)["valida"].mean() * 100).round(1).to_string())

    # 4. Características de cada polar válida
    print("\n4. Calculando las características de cada polar válida...")
    tabla = polares.groupby(["archivo", "reynolds"]).apply(caracteristicas, include_groups=False).reset_index()
    tabla = tabla.merge(perfiles, on="archivo")

    resumen = tabla.groupby("reynolds")[["cd_min", "cl_max", "ld_max", "pendiente"]].quantile([0.25, 0.5, 0.75])
    resumen = resumen.unstack()
    resumen.columns = pd.MultiIndex.from_tuples([(c, f"p{int(q * 100)}") for c, q in resumen.columns])
    print("   Medianas por Reynolds:")
    medianas = resumen.xs("p50", axis=1, level=1)
    print(medianas.round({"cd_min": 5, "cl_max": 3, "ld_max": 1, "pendiente": 4}).to_string())
    print(f"   Polares con el CL máximo en 20°: {tabla['cl_max_en_limite'].mean():.1%}")

    # 5. Comparación con la teoría del perfil delgado
    referencia = tabla[tabla["reynolds"] == RE_REFERENCIA]
    ajuste_alfa = np.polyfit(referencia["f_max"], np.radians(referencia["alfa_l0"]), 1)[0]
    ajuste_cm = np.polyfit(referencia["f_max"], referencia["cm0"], 1)[0]
    print(f"\n5. Teoría del perfil delgado (Re = {RE_REFERENCIA / 1e6:.0f}·10⁶, {len(referencia)} polares):")
    print(f"   dα_L0/df: XFOIL {ajuste_alfa:.2f} rad | teoría (línea media parabólica) -2.00 rad")
    print(f"   dCM/df:   XFOIL {ajuste_cm:.2f}     | teoría (línea media parabólica) {-np.pi:.2f}")
    simetricos = referencia[referencia["simetrico"]]
    print(f"   Perfiles simétricos: α_L0 medio {simetricos['alfa_l0'].abs().mean():.2f}° "
          f"y |CM| medio {simetricos['cm0'].abs().mean():.4f} (teoría: 0)")

    figura_reynolds(resumen, CARPETA_FIGURAS / "polares_reynolds.png")
    figura_teoria(referencia, CARPETA_FIGURAS / "teoria_perfil_delgado.png")
    print(f"\nFiguras guardadas en {CARPETA_FIGURAS}/")