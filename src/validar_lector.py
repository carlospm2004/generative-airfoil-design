# Pasa el lector por todos los .dat y resume los avisos.
# Los recuentos deben coincidir con docs/formato_dat.md.

from pathlib import Path

from lector import leer_perfil

CARPETA_PERFILES = Path("data/raw/coord_seligFmt")

lineas_no_validas = []
puntos_repetidos = []
x_fuera_de_rango = []
total = 0

for ruta in sorted(CARPETA_PERFILES.glob("*.dat")):
    perfil = leer_perfil(ruta)
    total += 1

    for aviso in perfil["avisos"]:
        if aviso.startswith("Línea no válida"):
            lista = lineas_no_validas
        elif aviso.startswith("Punto repetido"):
            lista = puntos_repetidos
        elif aviso.startswith("x fuera de"):
            lista = x_fuera_de_rango
        else:
            print(f"Aviso de tipo desconocido en {ruta.name}: {aviso}")
            continue

        if ruta.name not in lista:
            lista.append(ruta.name)

print(f"Perfiles leídos: {total}")
print(f"Línea no válida: {len(lineas_no_validas)} {lineas_no_validas}")
print(f"Punto repetido: {len(puntos_repetidos)} {puntos_repetidos}")
print(f"x fuera de [0, 1]: {len(x_fuera_de_rango)} {x_fuera_de_rango}")