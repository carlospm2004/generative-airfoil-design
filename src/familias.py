from pathlib import Path

import pandas as pd

RUTA_DESCRIPCIONES = Path("data/processed/descripciones.csv")
RUTA_SALIDA = Path("data/processed/familias.csv")

FAMILIAS = {
    "gottingen": "Historico",
    "eiffel": "Historico",
    "eppler": "E",
    "naca": "NACA",
    "nasa": "NASA",
    "naca-nasa": "NASA",
    "wortmann": "FX",
    "selig": "S",
    "drela": "AG",
    "martin": "MH",
    "quabeck": "HQ",
    "althaus": "AH",
    "rolf": "RG",
    "john": "EH",
    "boeing": "Boeing",
    "boeing-vertol": "Boeing-Vertol",
    "grumman": "Grumman",
    "lockheed-georgia": "Lockheed",
    "lockheed": "Lockheed",
    "sikorsky": "Sikorsky",
    "onera": "ONERA",
    "clark": "Clark",
    "rae": "RAE",
    "npl": "NPL",
    "roncz": "Roncz",
    "rutan": "Rutan",
    "lwk": "LWK",
    "marske": "Marske",
}

PREFIJOS = {
    "e": "E",
    "s": "S",
    "mh": "MH",
    "hq": "HQ",
}


def clave_descripcion(descripcion):
    primera_palabra = descripcion.split()[0].lower()
    return primera_palabra.split("/")[0]


def prefijo_archivo(archivo):
    prefijo = ""
    for letra in archivo:
        if letra.isdigit():
            break
        prefijo += letra
    return prefijo.lower()


def asignar_familia(fila):
    if pd.notna(fila["descripcion"]):
        clave = clave_descripcion(fila["descripcion"])
        return FAMILIAS.get(clave, "Otros")
    prefijo = prefijo_archivo(fila["archivo"])
    return PREFIJOS.get(prefijo, "Otros")


if __name__ == "__main__":
    if not RUTA_DESCRIPCIONES.exists():
        raise SystemExit(f"No existe {RUTA_DESCRIPCIONES}. Ejecuta antes descripciones.py")

    df = pd.read_csv(RUTA_DESCRIPCIONES)
    df["familia"] = df.apply(asignar_familia, axis=1)

    print(df["familia"].value_counts().to_string())
    con_nombre = (df["familia"] != "Otros").sum()
    print(f"\nCon familia: {con_nombre} de {len(df)} ({con_nombre / len(df):.1%})")

    sin_desc = df[df["descripcion"].isna()]
    print(f"Sin descripción asignados por prefijo: {(sin_desc['familia'] != 'Otros').sum()} de {len(sin_desc)}")

    df[["archivo", "familia"]].to_csv(RUTA_SALIDA, index=False)
    print(f"Guardado en {RUTA_SALIDA}")