# Calcula la polar de un perfil con XFOIL, lanzándolo desde Python.

import os
import subprocess
import tempfile
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

XFOIL = os.environ.get("XFOIL_PATH", "xfoil")
CARPETA_PERFILES = Path("data/processed/perfiles")

# Condiciones de cálculo
ALFA_MIN = -5.0
ALFA_MAX = 15.0
PASO_ALFA = 0.5
NCRIT = 9
ITERACIONES = 100
TIEMPO_MAXIMO = 60          # segundos por polar; si se supera, se da por fallida

COLUMNAS = ["alpha", "cl", "cd", "cdp", "cm", "top_xtr", "bot_xtr"]
LINEAS_CABECERA = 12        # líneas de texto antes de los datos en el archivo de la polar


def comandos_xfoil(reynolds):
    """Devuelve los comandos que se escriben en XFOIL, uno por línea."""
    return "\n".join([
        "PLOP", "G F", "",                              # desactiva la ventana de gráficos
        "LOAD perfil.dat",
        "PANE",                                         # remalla con 160 paneles
        "OPER",
        f"VISC {reynolds:.0f}",
        "VPAR", f"N {NCRIT}", "",                       # factor de transición
        f"ITER {ITERACIONES}",
        "PACC", "polar.txt", "",                        # polar a polar.txt, sin archivo de volcado
        f"ASEQ 0 {ALFA_MAX} {PASO_ALFA}",               # de 0° hacia arriba
        "INIT",                                         # reinicia la capa límite
        f"ASEQ {-PASO_ALFA} {ALFA_MIN} {-PASO_ALFA}",   # de -0,5° hacia abajo
        "PACC",
        "",
        "QUIT",
    ]) + "\n"


def leer_polar(ruta):
    """Lee el archivo de polar de XFOIL y lo devuelve como DataFrame ordenado por alpha."""
    if not ruta.exists():
        return pd.DataFrame(columns=COLUMNAS, dtype=float)
    lineas = ruta.read_text().splitlines()[LINEAS_CABECERA:]
    filas = [linea.split() for linea in lineas if linea.strip()]
    polar = pd.DataFrame(filas, columns=COLUMNAS, dtype=float)
    return polar.sort_values("alpha").drop_duplicates("alpha").reset_index(drop=True)


def calcular_polar(archivo, reynolds):
    """Calcula la polar de un perfil a un Reynolds.

    Devuelve (estado, polar, segundos), con estado "ok", "sin_convergencia" o "tiempo_agotado".
    """
    inicio = time.perf_counter()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
        carpeta = Path(carpeta)
        (carpeta / "perfil.dat").write_text((CARPETA_PERFILES / archivo).read_text())
        try:
            subprocess.run(
                [XFOIL],
                input=comandos_xfoil(reynolds),
                text=True,
                cwd=carpeta,
                capture_output=True,
                timeout=TIEMPO_MAXIMO,
            )
        except subprocess.TimeoutExpired:
            return "tiempo_agotado", pd.DataFrame(columns=COLUMNAS, dtype=float), time.perf_counter() - inicio
        polar = leer_polar(carpeta / "polar.txt")

    estado = "ok" if len(polar) > 0 else "sin_convergencia"
    return estado, polar, time.perf_counter() - inicio


if __name__ == "__main__":
    estado, polar, segundos = calcular_polar("naca2412.dat", 1e6)
    print(f"Estado: {estado} | {len(polar)} puntos | {segundos:.1f} s")
    print(polar.to_string(index=False))