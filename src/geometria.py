# Características geométricas de un perfil normalizado
# (BA en (0, 0), BS en (1, 0), orden Selig).

import numpy as np

N_REJILLA = 201


def separar_superficies(puntos):
    """Devuelve (extradós, intradós), ambos ordenados de x = 0 a x = 1."""
    distancias_origen = np.sqrt((puntos ** 2).sum(axis=1))
    i_ba = np.argmin(distancias_origen)

    extrados = puntos[: i_ba + 1][::-1]
    intrados = puntos[i_ba:]

    return extrados, intrados


def espesor_y_linea_media(puntos):
    """Devuelve la rejilla x, el espesor y la línea media en cada x."""
    extrados, intrados = separar_superficies(puntos)

    x = np.linspace(0, 1, N_REJILLA)
    y_extrados = np.interp(x, extrados[:, 0], extrados[:, 1])
    y_intrados = np.interp(x, intrados[:, 0], intrados[:, 1])

    espesor = y_extrados - y_intrados
    linea_media = (y_extrados + y_intrados) / 2

    return x, espesor, linea_media


def caracteristicas(puntos):
    """Devuelve un diccionario con t/c, x_t/c, f/c y x_f/c."""
    x, espesor, linea_media = espesor_y_linea_media(puntos)

    i_t = np.argmax(espesor)
    i_f = np.argmax(linea_media)

    return {
        "t_max": espesor[i_t],
        "x_t_max": x[i_t],
        "f_max": linea_media[i_f],
        "x_f_max": x[i_f],
    }


if __name__ == "__main__":
    from limpieza import limpiar_perfil

    for nombre in ["naca2412", "n0012", "clarky"]:
        perfil = limpiar_perfil(f"data/raw/coord_seligFmt/{nombre}.dat")
        print(nombre, caracteristicas(perfil["puntos"]))