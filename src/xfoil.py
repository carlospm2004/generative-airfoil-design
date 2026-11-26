# Calcula la polar de un perfil con XFOIL, lanzándolo desde Python.

import os
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

XFOIL = os.environ.get("XFOIL_PATH", "xfoil")
CARPETA_PERFILES = Path("data/processed/perfiles")

# Condiciones de cálculo
REYNOLDS = [5e4, 1e5, 2e5, 5e5, 1e6, 3e6, 6e6, 9e6]
ALFA_MIN = -5.0
ALFA_MAX = 20.0
PASO_ALFA = 0.5
NCRIT = 9
ITERACIONES = 100
N_PANELES = 160
TIEMPO_MAXIMO = 20          # segundos por polar; la más lenta del piloto tardó 10,5 s

# Barridos de alfa (inicio, fin, paso). Entre uno y otro se reinicia la capa límite (INIT).
BARRIDOS = [(0.0, ALFA_MAX, PASO_ALFA), (-PASO_ALFA, ALFA_MIN, -PASO_ALFA)]
# Reintento de la zona lineal, con paso más fino para que XFOIL encadene mejor las soluciones
BARRIDOS_REINTENTO = [(0.0, 10.5, 0.25), (-0.25, -2.0, -0.25)]

COLUMNAS = ["alpha", "cl", "cd", "cdp", "cm", "top_xtr", "bot_xtr"]
LINEAS_CABECERA = 12        # líneas de texto antes de los datos en el archivo de la polar


def comandos_xfoil(reynolds, n_paneles=N_PANELES, barridos=BARRIDOS):
    """Devuelve los comandos que se escriben en XFOIL, uno por línea."""
    comandos = [
        "PLOP", "G F", "",                              # desactiva la ventana de gráficos
        "LOAD perfil.dat",
        "PPAR", f"N {n_paneles}", "", "",               # número de paneles (dos Enter para salir)
        "PANE",                                         # remalla con ese número de paneles
        "OPER",
        f"VISC {reynolds:.0f}",
        "VPAR", f"N {NCRIT}", "",                       # factor de transición
        f"ITER {ITERACIONES}",
        "PACC", "polar.txt", "",                        # polar a polar.txt, sin archivo de volcado
    ]
    for i, (inicio, fin, paso) in enumerate(barridos):
        if i > 0:
            comandos.append("INIT")                     # reinicia la capa límite entre barridos
        comandos.append(f"ASEQ {inicio} {fin} {paso}")
    comandos += ["PACC", "", "QUIT"]
    return "\n".join(comandos) + "\n"


def leer_polar(ruta):
    """Lee el archivo de polar de XFOIL y lo devuelve como DataFrame ordenado por alpha."""
    if not ruta.exists():
        return pd.DataFrame(columns=COLUMNAS, dtype=float)
    lineas = ruta.read_text().splitlines()[LINEAS_CABECERA:]
    filas = [linea.split() for linea in lineas if linea.strip()]
    polar = pd.DataFrame(filas, columns=COLUMNAS, dtype=float)
    return polar.sort_values("alpha").drop_duplicates("alpha").reset_index(drop=True)


def calcular_polar(archivo, reynolds, n_paneles=N_PANELES, barridos=BARRIDOS):
    """Calcula la polar de un perfil a un Reynolds.

    Devuelve (estado, polar, segundos), con estado "ok", "sin_convergencia" o "tiempo_agotado".
    Una polar con "tiempo_agotado" puede traer los puntos calculados antes de que XFOIL se colgara.
    """
    inicio = time.perf_counter()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
        carpeta = Path(carpeta)
        (carpeta / "perfil.dat").write_text((CARPETA_PERFILES / archivo).read_text())
        try:
            subprocess.run(
                [XFOIL],
                input=comandos_xfoil(reynolds, n_paneles, barridos),
                text=True,
                cwd=carpeta,
                capture_output=True,
                timeout=TIEMPO_MAXIMO,
            )
            estado = "ok"
        except subprocess.TimeoutExpired:
            estado = "tiempo_agotado"
        # XFOIL escribe cada punto en el archivo según converge: si se ha colgado,
        # se recuperan los puntos que calculó antes de colgarse
        polar = leer_polar(carpeta / "polar.txt")

    if estado == "ok" and polar.empty:
        estado = "sin_convergencia"
    return estado, polar, time.perf_counter() - inicio


def combinar_polares(polar, reintento):
    """Añade a la polar los puntos del reintento que le faltan.

    Del reintento (paso de 0,25°) solo se toman los ángulos de la rejilla normal (múltiplos de 0,5°),
    para que todas las polares tengan los mismos ángulos. Si un ángulo está en las dos, se queda el original.
    """
    if reintento.empty:
        return polar
    pasos = reintento["alpha"] / PASO_ALFA
    en_rejilla = reintento[np.isclose(pasos, pasos.round())]
    combinada = pd.concat([polar, en_rejilla]) if not polar.empty else en_rejilla
    return combinada.drop_duplicates("alpha", keep="first").sort_values("alpha").reset_index(drop=True)


if __name__ == "__main__":
    estado, polar, segundos = calcular_polar("naca2412.dat", 1e6)
    print(f"Estado: {estado} | {len(polar)} puntos | {segundos:.1f} s")
    print(polar.to_string(index=False))