from pathlib import Path

import pandas as pd

RUTA_HTML = Path("data/raw/coord_database.html")
RUTA_PERFILES = Path("data/processed/perfiles")
RUTA_SALIDA = Path("data/processed/descripciones.csv")


def limpiar_texto(texto):
    texto = texto.split("<")[0]
    texto = texto.replace("&amp;", "&")
    texto = texto.strip()
    return texto


def leer_descripciones(ruta_html):
    try:
        texto = ruta_html.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        texto = ruta_html.read_text(encoding="latin-1")
    lineas = texto.splitlines()

    filas = []
    descripcion_anterior = None

    for linea in lineas:
        if "coord/" not in linea or '.dat"' not in linea:
            continue

        archivo = linea.split("coord/")[1].split('"')[0]
        descripcion = limpiar_texto(linea.split("\\")[1])

        if descripcion.lower() == "continued":
            descripcion = descripcion_anterior
        else:
            descripcion_anterior = descripcion

        filas.append({"archivo": archivo, "descripcion": descripcion})

    return pd.DataFrame(filas)


if __name__ == "__main__":
    if not RUTA_HTML.exists():
        raise SystemExit(f"No existe {RUTA_HTML}. Guarda ahí la página de la UIUC.")

    df = leer_descripciones(RUTA_HTML)
    print(f"Descripciones en la web: {len(df)}")
    print(f"Archivos repetidos en la web: {df['archivo'].duplicated().sum()}")
    print(f"Quedan 'continued': {(df['descripcion'].str.lower() == 'continued').sum()}")
    df = df.drop_duplicates(subset="archivo", keep="first")

    procesados = sorted(ruta.name for ruta in RUTA_PERFILES.glob("*.dat"))
    df_procesados = pd.DataFrame({"archivo": procesados})
    df_final = df_procesados.merge(df, on="archivo", how="left")

    con = df_final["descripcion"].notna().sum()
    sin = df_final["descripcion"].isna().sum()
    print(f"Perfiles procesados: {len(df_final)}")
    print(f"  con descripción: {con}")
    print(f"  sin descripción: {sin}")

    df_final.to_csv(RUTA_SALIDA, index=False)
    print(f"Guardado en {RUTA_SALIDA}")