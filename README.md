# Airfoil AI

**Diseño aerodinámico asistido por IA: de los datos de perfiles de ala a un asistente de diseño inteligente.**

> 🚧 Proyecto en desarrollo — proyecto propio del Máster en Inteligencia Artificial y Big Data (EDEM, Valencia).

## ¿Qué es un perfil aerodinámico?

Si cortamos el ala de un avión o de un dron como si fuera una barra de pan, la forma de la sección que vemos se llama perfil aerodinámico. Esa forma decide cuánto sustenta el ala, cuánta resistencia genera y cómo se comporta en vuelo.

Existen miles de perfiles publicados, y no hay uno "mejor" que los demás: cada aplicación (un planeador, un dron de largo alcance, una hélice, una turbina eólica…) necesita un compromiso distinto. Elegir o diseñar el perfil adecuado es lento, porque cada candidato hay que analizarlo con un simulador.

## ¿Qué quiero hacer?

Construir, paso a paso, un sistema que:

1. Reúna y organice los datos de unos 1.650 perfiles reales a partir de una base de datos pública.
2. Calcule su rendimiento de forma automática con un simulador aerodinámico gratuito (XFOIL).
3. Permita explorar los datos con una herramienta visual.
4. Prediga el rendimiento al instante, sin tener que simularlo, de perfiles que no formen parte del conjunto de datos inicial.
5. Diseñe perfiles nuevos a partir de unos requisitos.
6. Asista al ingeniero mediante un sistema multiagente que entienda lo que se pide, proponga diseños, los compruebe y explique el resultado.

La idea es ir avanzando por fases, aplicando en cada una lo que vamos viendo en el máster.

## Alcance

El proyecto se centra en **perfiles para aeronaves de ala fija en régimen subsónico**, con números de Reynolds entre 5·10⁴ y 3·10⁶: drones, alas volantes, planeadores y aviación ligera.

Es el régimen en el que XFOIL, el simulador del proyecto, es fiable. Los aviones comerciales vuelan a velocidades transónicas, donde aparecen ondas de choque que XFOIL no puede modelar.

La base de datos conserva todos los perfiles válidos, incluidos los de hélices, rotores y turbinas eólicas: aportan variedad de formas al modelo. Cada perfil guarda su descripción original, por si más adelante se quiere filtrar por aplicación.

## Pasos que voy a seguir

### Fase 1 — Datos ✅

Con Python:

- [x] Descargar la base de datos de perfiles de la Universidad de Illinois (UIUC).
- [x] Leer cada archivo de coordenadas y detectar los que vengan con errores o formatos raros.
- [x] Limpiar y normalizar todos los perfiles a un formato común (ver [`docs/limpieza.md`](docs/limpieza.md)).
- [x] Calcular características de cada perfil: espesor, curvatura y otras propiedades geométricas (ver [`docs/geometria.md`](docs/geometria.md)).
- [x] Clasificar los perfiles por familia (diseñador o serie), a partir de la descripción de cada perfil en la web de la UIUC, y reunirlo todo en un catálogo final (ver [`docs/clasificacion.md`](docs/clasificacion.md)).

> La clasificación por uso (planeador, hélice, turbina eólica…) se descartó: solo el 24 % de las descripciones lo indican. Queda como posible proyecto de aprendizaje automático: predecir el uso de un perfil a partir de su geometría.

### Base de datos ✅

- [x] Montar una base de datos PostgreSQL en Docker y cargar en ella el catálogo y las coordenadas de todos los perfiles (ver [`docs/base-datos.md`](docs/base-datos.md)).

### Herramienta de visualización ✅

Una interfaz para explorar los datos, con dos partes: una API (backend) que consulta la base de datos y una interfaz web (frontend) que muestra los resultados:

- Catálogo de perfiles, filtrable por familia y características.
- Ficha de cada perfil, con su forma dibujada y sus datos.
- Comparador para superponer varios perfiles y ver sus diferencias.
- Mapa del dataset, donde cada punto es un perfil y se pueden ver agrupaciones.

Avance:

- [x] API con FastAPI para consultar el catálogo, la ficha y las coordenadas de cada perfil (ver [`docs/api.md`](docs/api.md)).
- [x] Interfaz web con catálogo, ficha, comparador y mapa del dataset (ver [`docs/frontend.md`](docs/frontend.md)).

La herramienta irá creciendo con el proyecto: en cada fase se le añadirán los nuevos resultados, hasta convertirse en la interfaz final.

### Fase 2 — Generación de datos a gran escala

- [ ] Automatizar el simulador para calcular el rendimiento de todos los perfiles en distintas condiciones de vuelo.
- [ ] Filtrar los casos en los que la simulación falla.
- [ ] Guardar todos los resultados en una base de datos y analizarlos.

### Fase 3 — Predicción del rendimiento

- [ ] Entrenar un modelo que, a partir de la forma de un perfil que no esté en el conjunto de datos inicial, prediga su rendimiento al instante.

### Fase 4 — Diseño de perfiles nuevos

- [ ] Desarrollar un modelo capaz de proponer perfiles nuevos que cumplan unos requisitos.
- [ ] Validar siempre los diseños propuestos con el simulador.

### Fase 5 — Asistente multiagente

- [ ] Crear un sistema de agentes que funcione como un equipo de ingenieros virtuales: uno interpreta lo que pide el usuario, otro diseña, otro comprueba los resultados y otro redacta las conclusiones.

### Fase 6 — Despliegue

- [ ] Publicar la herramienta como aplicación web.

> Las técnicas concretas de cada fase se decidirán a medida que se vean en el máster.

## Cómo obtener los datos

Los datos no se incluyen en el repositorio: se descargan de la fuente original y se preparan con scripts.

### 1. Preparar el entorno

Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/Scripts/activate      # Git Bash (en PowerShell: .venv\Scripts\activate)
pip install -r requirements.txt
```

### 2. Descargar los perfiles

Descarga [coord_seligFmt.zip](https://m-selig.ae.illinois.edu/ads/archives/coord_seligFmt.zip) desde el navegador y guárdalo en la carpeta `data/` de la raíz del repositorio (créala si no existe). La web de la UIUC bloquea las descargas automáticas, por eso este paso es manual.

Guarda también la página [coord_database.html](https://m-selig.ae.illinois.edu/ads/coord_database.html) desde el navegador (Guardar como → solo HTML) en `data/raw/coord_database.html`. De ella se sacan las descripciones de los perfiles.

### 3. Generar los datos

Con el entorno virtual activado, desde la raíz del repositorio:

```bash
python src/preparar_datos_uiuc.py   # descomprime los 1.665 perfiles en data/raw/
python src/generar_procesados.py    # limpia y normaliza: 1.656 perfiles en data/processed/perfiles/
python src/validar_limpieza.py      # comprueba la limpieza y genera data/processed/resumen_limpieza.csv
python src/calcular_geometria.py    # características geométricas en data/processed/geometria.csv
python src/validar_geometria.py     # comprueba la geometría con los NACA de 4 cifras
python src/descripciones.py         # descripciones de la web en data/processed/descripciones.csv
python src/familias.py              # familia de cada perfil en data/processed/familias.csv
python src/generar_catalogo.py      # catálogo final en data/processed/perfiles.csv
```

Resultados con la versión de febrero de 2026 de la base de datos: **1.665 perfiles originales**, 9 excluidos y **1.656 perfiles limpios**, todos validados, con sus características geométricas y su familia. El catálogo final es `data/processed/perfiles.csv`.

### 4. Cargar la base de datos y arrancar la aplicación

Hace falta tener [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y abierto. Desde la raíz del repositorio:

```bash
cp .env.example .env               # y cambia la contraseña en .env
docker compose up -d --build       # levanta PostgreSQL (crea las tablas), la API y la interfaz web
python src/cargar_bd.py            # carga el catálogo y las coordenadas, y valida la carga
```

Resultado: **1.656 perfiles** en la tabla `perfiles` y **110.767 puntos** en la tabla `coordenadas`. El script se puede ejecutar tantas veces como se quiera: cada vez vacía las tablas y las vuelve a cargar.

La interfaz web queda en [`http://localhost:8080`](http://localhost:8080). La API, en `http://localhost:8000`, con su documentación interactiva en [`http://localhost:8000/docs`](http://localhost:8000/docs).

Para pararlo todo sin perder los datos: `docker compose down`.

## Estructura del repositorio

```
├── api/                   ← API (FastAPI), un servicio aparte con su propia imagen de Docker
│   ├── main.py            ← endpoints
│   ├── bd.py              ← conexión y consultas a PostgreSQL
│   ├── Dockerfile         ← imagen de la API
│   └── requirements.txt   ← dependencias solo de la API
├── data/                  ← datos (no se suben; se regeneran con los scripts)
│   ├── raw/               ← perfiles originales y página de la UIUC
│   └── processed/         ← perfiles limpios y tablas resumen
├── docs/                  ← análisis y decisiones del proyecto
│   ├── formato_dat.md     ← análisis del formato de los archivos originales
│   ├── limpieza.md        ← proceso de limpieza y normalización
│   ├── geometria.md       ← características geométricas y su validación
│   ├── clasificacion.md   ← familias y catálogo final
│   ├── base-datos.md      ← base de datos: esquema, carga y validación
│   ├── api.md             ← API: endpoints, decisiones y Docker
│   └── frontend.md        ← interfaz web: vistas, arquitectura y Docker
├── frontend/              ← interfaz web, servida por nginx
│   ├── web/               ← index.html, estilos.css y app.js
│   ├── nginx.conf         ← sirve la web y reenvía /api a la API
│   └── Dockerfile         ← imagen del frontend
├── notebooks/             ← exploración
├── sql/
│   └── esquema.sql        ← tablas de la base de datos
├── src/                   ← código
│   ├── lector.py          ← lee un .dat y detecta anomalías
│   ├── limpieza.py        ← exclusiones, duplicados y normalización
│   ├── geometria.py       ← espesor, curvatura, borde de salida y área
│   ├── familias.py        ← familia de cada perfil a partir de su descripción
│   ├── cargar_bd.py       ← carga el catálogo y las coordenadas en PostgreSQL
│   └── ...                ← scripts de preparación, generación y validación
├── docker-compose.yml     ← servicios de PostgreSQL, la API y la interfaz web
├── .env.example           ← plantilla de las variables de entorno (copiar a .env)
└── requirements.txt       ← dependencias de Python
```

## Fuentes de datos

- [UIUC Airfoil Coordinates Database](https://m-selig.ae.illinois.edu/ads/coord_database.html): geometría de unos 1.650 perfiles reales.
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/): simulador aerodinámico gratuito para calcular el rendimiento de los perfiles.