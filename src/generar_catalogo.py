from pathlib import Path

import pandas as pd

RUTA_GEOMETRIA = Path("data/processed/geometria.csv")
RUTA_DESCRIPCIONES = Path("data/processed/descripciones.csv")
RUTA_FAMILIAS = Path("data/processed/familias.csv")
RUTA_SALIDA = Path("data/processed/perfiles.csv")

if __name__ == "__main__":
    for ruta in [RUTA_GEOMETRIA, RUTA_DESCRIPCIONES, RUTA_FAMILIAS]:
        if not ruta.exists():
            raise SystemExit(f"No existe {ruta}. Genera antes los pasos anteriores.")

    geometria = pd.read_csv(RUTA_GEOMETRIA)
    descripciones = pd.read_csv(RUTA_DESCRIPCIONES)
    familias = pd.read_csv(RUTA_FAMILIAS)

    catalogo = geometria.merge(descripciones, on="archivo", how="left", validate="one_to_one")
    catalogo = catalogo.merge(familias, on="archivo", how="left", validate="one_to_one")

    columnas = ["archivo", "nombre", "familia", "descripcion"]
    resto = [c for c in catalogo.columns if c not in columnas]
    catalogo = catalogo[columnas + resto]

    print(f"Filas: {len(catalogo)} (geometría: {len(geometria)})")
    print(f"Sin familia (NaN): {catalogo['familia'].isna().sum()}")
    print(f"Sin descripción: {catalogo['descripcion'].isna().sum()}")
    print(f"Columnas: {list(catalogo.columns)}")

    catalogo.to_csv(RUTA_SALIDA, index=False)
    print(f"Guardado en {RUTA_SALIDA}")