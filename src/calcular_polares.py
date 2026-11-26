# Cálculo completo de la Fase 2: polares de todos los perfiles a todos los Reynolds con XFOIL.
# Si una polar sale no válida pero tiene puntos, se reintenta la zona lineal con paso más fino.
# Cada resultado se guarda en la base de datos nada más calcularse, y los que ya están
# guardados se saltan: si el cálculo se corta (Ctrl+C, apagón...), basta con volver a lanzarlo.
#
# Uso:
#   python src/calcular_polares.py        # todos los perfiles
#   python src/calcular_polares.py 3      # solo los 3 primeros perfiles pendientes (prueba)

import sys
import time

import pandas as pd
from psycopg2.extras import execute_values

from cargar_bd import conectar
from polares import calidad_polar, marcar_post_perdida
from xfoil import ALFA_MAX, BARRIDOS_REINTENTO, REYNOLDS, calcular_polar, combinar_polares

COLUMNAS_CALCULOS = [
    "archivo", "reynolds", "estado", "segundos", "n_puntos", "cobertura_lineal",
    "hueco_lineal", "alfa_cl_max", "cl_max_en_limite", "valida", "reintento",
]
COLUMNAS_POLARES = [
    "archivo", "reynolds", "alpha", "cl", "cd", "cdp", "cm", "top_xtr", "bot_xtr", "post_perdida",
]


def pendientes(cur):
    """Devuelve, por perfil, la lista de Reynolds que aún no están en la tabla calculos."""
    cur.execute("SELECT archivo FROM perfiles ORDER BY archivo")
    archivos = [fila[0] for fila in cur.fetchall()]
    cur.execute("SELECT archivo, reynolds FROM calculos")
    hechos = set(cur.fetchall())
    por_perfil = {}
    for archivo in archivos:
        faltan = [re for re in REYNOLDS if (archivo, int(re)) not in hechos]
        if faltan:
            por_perfil[archivo] = faltan
    return por_perfil


def calcular_con_reintento(archivo, reynolds):
    """Calcula la polar y, si no es válida pero tiene puntos, reintenta la zona lineal y combina."""
    estado, polar, segundos = calcular_polar(archivo, reynolds)
    if polar.empty or calidad_polar(polar, ALFA_MAX)["valida"]:
        return estado, polar, segundos, False
    _, extra, segundos_extra = calcular_polar(archivo, reynolds, barridos=BARRIDOS_REINTENTO)
    return estado, combinar_polares(polar, extra), segundos + segundos_extra, True


def guardar(conn, archivo, reynolds, estado, polar, segundos, reintento):
    """Guarda un cálculo y sus puntos en una sola transacción."""
    calidad = calidad_polar(polar, ALFA_MAX)
    fila = {"archivo": archivo, "reynolds": int(reynolds), "estado": estado, "segundos": segundos,
            "reintento": reintento, **calidad}
    valores = tuple(None if pd.isna(fila[c]) else fila[c] for c in COLUMNAS_CALCULOS)   # NaN -> NULL

    puntos = []
    if not polar.empty:
        df = marcar_post_perdida(polar).assign(archivo=archivo, reynolds=int(reynolds))[COLUMNAS_POLARES]
        puntos = list(df.astype(object).itertuples(index=False, name=None))     # tipos de Python

    with conn:                                   # commit al salir; rollback si hay un error
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO calculos ({', '.join(COLUMNAS_CALCULOS)}) "
                f"VALUES ({', '.join(['%s'] * len(COLUMNAS_CALCULOS))})",
                valores,
            )
            if puntos:
                execute_values(cur, f"INSERT INTO polares ({', '.join(COLUMNAS_POLARES)}) VALUES %s", puntos)
    return calidad["valida"]


def formato_tiempo(segundos):
    horas, resto = divmod(int(segundos), 3600)
    return f"{horas} h {resto // 60:02d} min"


if __name__ == "__main__":
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None

    conn = conectar()
    with conn.cursor() as cur:
        por_perfil = pendientes(cur)
    if limite:
        por_perfil = dict(list(por_perfil.items())[:limite])

    total = sum(len(faltan) for faltan in por_perfil.values())
    print(f"Pendientes: {len(por_perfil)} perfiles, {total} polares")
    if total == 0:
        print("No queda nada por calcular.")
        sys.exit()

    hechas = validas = 0
    inicio = time.perf_counter()
    try:
        for i, (archivo, faltan) in enumerate(por_perfil.items(), start=1):
            for reynolds in faltan:
                estado, polar, segundos, reintento = calcular_con_reintento(archivo, reynolds)
                validas += guardar(conn, archivo, reynolds, estado, polar, segundos, reintento)
                hechas += 1
            transcurrido = time.perf_counter() - inicio
            restante = transcurrido / hechas * (total - hechas)
            print(f"[{i}/{len(por_perfil)}] {archivo:22s} {hechas}/{total} polares | "
                  f"válidas {validas / hechas:.0%} | {formato_tiempo(transcurrido)} | quedan ~{formato_tiempo(restante)}")
    except KeyboardInterrupt:
        print("\nCálculo interrumpido. Lo calculado está guardado: vuelve a lanzar el script para continuar.")
    finally:
        conn.close()

    print(f"\nCalculadas en esta ejecución: {hechas} polares en {formato_tiempo(time.perf_counter() - inicio)}")