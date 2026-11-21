# Clasificación de los perfiles

Asignación de una familia a cada uno de los 1.656 perfiles limpios y unión de todos los datos en el catálogo final de la Fase 1: `data/processed/perfiles.csv`, con una fila por perfil.

La geometría que se incluye en el catálogo está explicada en [`geometria.md`](geometria.md).

## Resumen

| Etapa | Resultado | Script |
|---|---|---|
| Descripciones de la web de la UIUC | 1.581 de 1.656 perfiles con descripción | `descripciones.py` |
| Familia por diseñador | 25 familias; 1.392 perfiles (84,1 %) con familia con nombre | `familias.py` |
| Catálogo final | 1.656 filas: familia, descripción y geometría | `generar_catalogo.py` |

## 1. Descripciones

La web de la UIUC ([coord_database.html](https://m-selig.ae.illinois.edu/ads/coord_database.html)) tiene una línea por perfil, con los campos separados por `\`:

```
<a href=".../coord/2032c.dat">2032c.dat</a> \ Dillner 20-32-C low Reynolds number airfoil \ <a href=".../2032c.gif">...
```

`descripciones.py` toma el nombre del archivo del enlace (`coord/…dat`) y la descripción del segundo campo. La página se guarda a mano en `data/raw/coord_database.html`, igual que el zip de los perfiles, porque la web bloquea las descargas automáticas.

### Decisiones

- **Líneas "continued" (32).** Algunas series ocupan varias líneas y solo la primera lleva la descripción; el resto dicen `continued`. Por ejemplo, `b707b`–`b707e` siguen a `b707a` (Boeing 707). Como la página está en orden alfabético, cada `continued` hereda la descripción de la línea anterior. Resultado: 0 `continued` en la tabla.
- **Restos de HTML.** Algunas descripciones llevan un enlace pegado (`Selig S1010 HPV airfoil, Wayback Machine: <a …>`), así que se corta el texto en el primer `<`. La única entidad HTML que aparece es `&amp;` (5 casos, por ejemplo *Fage & Collins*), y se sustituye por `&`.
- **Archivo repetido.** `sc20714.dat` aparece dos veces en la web, con dos descripciones equivalentes del mismo perfil NASA SC(2)-0714. Se conserva la primera.
- **Codificación.** Según el navegador, la página se guarda en UTF-8 o en Latin-1 (la `ü` de nombres como Würz o Wortmann). El script prueba UTF-8 y, si falla, lee en Latin-1.

### Resultado

| | Perfiles |
|---|---|
| Líneas de perfil en la web | 1.595 (1.594 archivos distintos) |
| Perfiles procesados con descripción | 1.581 |
| Perfiles procesados sin descripción | 75 |

Los 75 sin descripción son archivos que están en el zip pero no en la página (`as6091`–`as6099`, `hor04`, `ist-mt1-12`, `s8064`…).

## 2. Familias

### Por qué la descripción y no el nombre del archivo

La primera idea era sacar la familia del prefijo del nombre del archivo, pero varios prefijos son ambiguos:

| Prefijo | Diseñadores distintos |
|---|---|
| `sc` | Sikorsky (rotor) y NASA (supercríticos SC(2)) |
| `ah` | Dieter Althaus y Andrew Hollom |
| `b`, `c`, `l`, `n` | Varias empresas o series |

La descripción de la web casi siempre empieza por el diseñador o la organización (`Eppler E1098…`, `Wortmann FX 05-188…`, `Sikorsky SC1095…`), así que la familia se toma de la **primera palabra de la descripción**.

### Método

1. Se toma la primera palabra de la descripción en minúsculas y se corta en la primera `/`. Así, las colaboraciones se unen a su organización: `Sikorsky/Velkoff`, `NACA/Munk`, `Boeing-Vertol/Dadone`…
2. Un diccionario traduce esa palabra a un nombre de familia. Se usan las iniciales con las que se conoce cada serie: `martin` (Martin Hepperle) → `MH`, `rolf` (Rolf Girsberger) → `RG`, `john` (John Yost) → `EH`, `wortmann` → `FX`…
3. Para los 75 perfiles sin descripción se usa el prefijo del archivo, pero solo en los prefijos comprobados como no ambiguos dentro de ese grupo: `e` → E, `s` → S, `mh` → MH, `hq` → HQ. Así se asignan 15 de los 75.
4. Todo lo demás va a **Otros**.

### Decisiones

- **Umbral de 5 perfiles.** Hay 201 palabras iniciales distintas, pero están muy concentradas: las 25 primeras cubren el 84 % de los perfiles con descripción. Solo se crea una familia si reúne 5 o más perfiles, porque una familia de 2–3 no aporta nada al análisis. El umbral está en el propio diccionario: solo contiene esas palabras.
- **NACA y NASA, separadas.** `naca` y `naca/munk` van a **NACA**: los perfiles clásicos de 4 y 5 cifras y la serie 6. `nasa`, `nasa/langley` y `naca-nasa` (las modificaciones de Hicks en NASA Ames) van a **NASA**: supercríticos, LS, NLF…
- **Boeing y Boeing-Vertol, separadas.** Boeing son perfiles de ala fija, y Boeing-Vertol, de palas de rotor.
- **Histórico.** Göttingen (397) y Eiffel (5) se agrupan como **Historico** (ver sección 4).
- **`university` (5) sin familia.** Pasa el umbral, pero mezcla universidades distintas (Illinois, Glasgow…): no es una familia de diseño.

### Resultado

| Familia | Perfiles | Familia | Perfiles |
|---|---|---|---|
| Historico | 402 | Grumman | 16 |
| Otros | 264 | Lockheed | 14 |
| E (Eppler) | 200 | RG (Girsberger) | 12 |
| NACA | 170 | Clark | 11 |
| FX (Wortmann) | 111 | ONERA | 10 |
| S (Selig) | 100 | EH (Yost) | 9 |
| AG (Drela) | 67 | Sikorsky | 8 |
| NASA | 59 | RAE | 8 |
| MH (Hepperle) | 52 | Roncz | 6 |
| HQ (Quabeck) | 43 | NPL | 6 |
| AH (Althaus) | 37 | Rutan | 5 |
| Boeing | 19 | LWK | 5 |
| Boeing-Vertol | 17 | Marske | 5 |

**Comprobación de los prefijos ambiguos:**

- `sc`: 21 perfiles en NASA y 5 en Sikorsky.
- `ah`: 37 en AH (Althaus), y los 2 de Andrew Hollom en Otros.

**Cobertura: 84,1 %.** El objetivo inicial era del 85 %, pero se fijó antes de ver la cola de la distribución. Los 264 perfiles de Otros se reparten entre más de 170 diseñadores con 1–4 perfiles cada uno; llegar al 85 % exigiría añadir unas 15 familias de 1–2 perfiles, justo lo que el umbral descarta.

## 3. Clasificación por uso: descartada

También se planteó clasificar los perfiles por uso (planeador, ala volante, hélice, turbina eólica…) a partir de palabras clave de la descripción. Se descartó porque **solo 403 de los 1.656 perfiles (24 %)** mencionan su uso, y 97 de ellos mencionan más de uno. Una columna "uso" vacía en tres de cada cuatro perfiles parecería completa sin serlo.

La descripción se conserva en el catálogo. Queda abierta como posible proyecto de aprendizaje automático: entrenar un modelo con los perfiles que sí indican su uso y predecir el uso del resto a partir de su geometría.

## 4. Coherencia física de las familias

Las medianas de geometría por familia tienen sentido aerodinámico, lo que valida la clasificación desde un ángulo independiente:

| Familia | `t_max` mediana | `f_max` mediana | Interpretación |
|---|---|---|---|
| AG (Drela) | 7,3 % | 2,1 % | Los más finos: veleros de radiocontrol y de lanzamiento a mano |
| Grumman | 8,5 % | 1,3 % | Ala transónica de reactor ejecutivo: fina y poco curvada |
| NACA / NASA | 12 % | 1,6–1,8 % | Perfiles de referencia de la aviación; NACA tiene 39 de los 125 simétricos |
| Historico | 10,8 % | 5,0 % | La mayor curvatura: alas de baja velocidad de 1910–1930 |
| FX, AH | 14–15 % | 3,7–3,8 % | Planeadores de altas prestaciones: espesor para la estructura y curvatura para sustentar mucho |

### Advertencia para la Fase 2: el peso de los perfiles históricos

Los 397 perfiles Göttingen son una serie de ensayos en túnel del AVA de Göttingen (el instituto de Prandtl) de los años 10–30. Son datos válidos, pero suponen el **24 % del catálogo** y representan otra época del diseño:

- Su curvatura mediana (5 %) es más del doble que la de NACA (1,8 %).
- 43 de los 100 perfiles más curvados de la base son históricos.

Un modelo entrenado con toda la base aprendería de ellos en una cuarta parte de los casos y tendería a perfiles más curvados que los actuales. La familia `Historico` permite filtrarlos con una línea y comparar los resultados con y sin ellos.

## 5. Catálogo final

`generar_catalogo.py` une las tres tablas por la columna `archivo`, partiendo de la geometría, que define los 1.656 perfiles válidos. Los `merge` llevan `validate="one_to_one"`: si un archivo apareciera repetido en alguna tabla, el script se pararía en lugar de duplicar filas.

| Columna | Contenido |
|---|---|
| `archivo` | Nombre del archivo `.dat` |
| `nombre` | Nombre de la cabecera del archivo |
| `familia` | Familia asignada (sección 2) |
| `descripcion` | Descripción de la web de la UIUC; vacía en 75 perfiles |
| `t_max` … `simetrico` | Características geométricas (ver [`geometria.md`](geometria.md)) |

## Limitaciones conocidas

- **Otros (264 perfiles, 16 %)** mezcla diseñadores muy distintos y no debe tratarse como una familia.
- **Historico** agrupa por época, no por diseñador.
- Solo **15 de los 75 perfiles sin descripción** tienen familia; los demás van a Otros, porque es mejor no asignar familia que asignar una equivocada.

## Cómo reproducirlo

Guarda la página [coord_database.html](https://m-selig.ae.illinois.edu/ads/coord_database.html) desde el navegador en `data/raw/coord_database.html`. Después, desde la raíz del repositorio, con el entorno virtual activado y la geometría ya calculada:

```bash
python src/descripciones.py       # data/processed/descripciones.csv
python src/familias.py            # data/processed/familias.csv
python src/generar_catalogo.py    # data/processed/perfiles.csv
```