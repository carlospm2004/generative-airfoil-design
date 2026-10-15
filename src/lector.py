# Lector de archivos .dat de la UIUC (formato Selig).
# Especificación: docs/formato_dat.md

from pathlib import Path

TOLERANCIA_X = 0.001


def leer_perfil(ruta):
    """Lee un .dat y devuelve un diccionario con el nombre, los puntos y los avisos."""
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()

    nombre = lineas[0].strip()

    puntos = []
    avisos = []

    for linea in lineas[1:]:
        texto = linea.strip()

        if texto == "" or texto.startswith("#"):
            continue

        trozos = texto.split()

        if len(trozos) != 2:
            avisos.append(f"Línea no válida: {texto}")
            continue

        try:
            x = float(trozos[0])
            y = float(trozos[1])
        except ValueError:
            avisos.append(f"Línea no válida: {texto}")
            continue

        puntos.append((x, y))

    # Puntos consecutivos repetidos
    for i in range(len(puntos) - 1):
        if puntos[i] == puntos[i + 1]:
            avisos.append(f"Punto repetido en la posición {i + 1}: {puntos[i]}")

    # x fuera de [0, 1]
    if puntos:
        xs = [p[0] for p in puntos]
        if min(xs) < -TOLERANCIA_X or max(xs) > 1 + TOLERANCIA_X:
            avisos.append(f"x fuera de [0, 1]: de {min(xs)} a {max(xs)}")

    return {"nombre": nombre, "puntos": puntos, "avisos": avisos}


if __name__ == "__main__":
    perfil = leer_perfil("data/raw/coord_seligFmt/vr8b.dat")
    print(perfil["nombre"])
    print(len(perfil["puntos"]), "puntos")
    print(perfil["avisos"])
