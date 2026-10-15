# Descomprime la base de datos de perfiles de la UIUC (formato Selig)
# en data/raw/ y cuenta los perfiles.
#
# El zip hay que descargarlo a mano desde el navegador, porque la web
# de la UIUC bloquea las descargas automáticas.

import zipfile
from pathlib import Path

URL_ZIP = "https://m-selig.ae.illinois.edu/ads/archives/coord_seligFmt.zip"
CARPETA_DATOS = Path("data")
CARPETA_RAW = CARPETA_DATOS / "raw"
RUTA_ZIP = CARPETA_DATOS / "coord_seligFmt.zip"

# 1. Crear las carpetas si no existen
CARPETA_RAW.mkdir(parents=True, exist_ok=True)

# 2. Comprobar que el zip está
if not RUTA_ZIP.exists():
    raise SystemExit(
        f"No se encuentra {RUTA_ZIP}\n"
        f"Descárgalo con el navegador desde:\n  {URL_ZIP}\n"
        f"y guárdalo en la carpeta {CARPETA_DATOS}/"
    )

# 3. Comprobar que es un zip válido
if not zipfile.is_zipfile(RUTA_ZIP):
    raise SystemExit(
        f"{RUTA_ZIP} no es un zip válido. "
        f"Bórralo y vuelve a descargarlo desde el navegador."
    )

# 4. Descomprimir en data/raw/
with zipfile.ZipFile(RUTA_ZIP) as z:
    z.extractall(CARPETA_RAW)

# 5. Contar los perfiles
archivos_dat = list(CARPETA_RAW.rglob("*.dat"))
print(f"Perfiles encontrados: {len(archivos_dat)}")