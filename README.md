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

## Pasos que voy a seguir

### Fase 1 — Datos (en curso)

Con Python:

- [ ] Descargar la base de datos de perfiles de la Universidad de Illinois (UIUC).
- [ ] Leer cada archivo de coordenadas y detectar los que vengan con errores o formatos raros.
- [ ] Limpiar y normalizar todos los perfiles a un formato común.
- [ ] Calcular características de cada perfil: espesor, curvatura y otras propiedades geométricas.
- [ ] Clasificar los perfiles:
  - por familia, a partir del nombre del archivo;
  - por uso (planeador, ala volante, hélice, turbina eólica…), extrayendo la descripción de cada perfil de la web de la UIUC.

### Herramienta de visualización

En cuanto los datos estén limpios, crearé una interfaz para explorarlos:

- Catálogo de perfiles, filtrable por familia, uso y características.
- Ficha de cada perfil, con su forma dibujada y sus datos.
- Comparador para superponer varios perfiles y ver sus diferencias.
- Mapa del dataset, donde cada punto es un perfil y se pueden ver agrupaciones.

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


## Fuentes de datos

- [UIUC Airfoil Coordinates Database](https://m-selig.ae.illinois.edu/ads/coord_database.html): geometría de unos 1.650 perfiles reales.
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/): simulador aerodinámico gratuito para calcular el rendimiento de los perfiles.


