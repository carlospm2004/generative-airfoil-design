# Limpieza y normalización de los perfiles

Proceso que convierte los 1.665 archivos originales de la UIUC (`data/raw/coord_seligFmt/`) en 1.656 perfiles limpios con un formato común (`data/processed/perfiles/`).

El análisis previo del formato, del que salen los criterios de esta limpieza, está en [`formato_dat.md`](formato_dat.md).

## Resumen

| Etapa | Perfiles | Script |
|---|---|---|
| Archivos originales | 1.665 | `preparar_datos_uiuc.py` |
| Excluidos | 9 | `limpieza.py` (`EXCLUIDOS`) |
| Limpios y normalizados | **1.656** | `generar_procesados.py` |
| Validados | 1.656 / 1.656 | `validar_limpieza.py` |

## 1. Exclusiones (9 archivos)

Se excluyen los archivos que no son perfiles de un solo elemento, porque XFOIL solo analiza perfiles de un elemento:

| Archivo | Motivo |
|---|---|
| `naca1.dat` | Carenado de motor (*NACA-1 cowl*), no es un perfil: curva abierta de (1, 1) a (0, 0) |
| `30p-30n.dat` | Configuración multielemento completa (slat + principal + flap) en un único archivo |
| `30p-30n-slat.dat`, `30p-30n-main.dat`, `30p-30n-flap.dat` | Elementos de la configuración 30P-30N |
| `r1145msf.dat`, `r1145msm.dat` | Flap y elemento principal del Roncz R1145MS |
| `ua79sff.dat`, `ua79sfm.dat` | Flap y elemento principal del UA 79-SF-187 |

La exclusión se hace por nombre de archivo, no por la cabecera: la cabecera de `ua79sff.dat` dice "MAIN ELEMENT", aunque es el flap.

`s1221-4deg-flap.dat` **no** se excluye: es un único contorno con el flap ya deflectado.

**Se conservan** los perfiles de turbina eólica, hélice y rotor. La limpieza elimina lo que está mal, no lo que queda fuera del alcance del proyecto; filtrar por aplicación es una decisión posterior y reversible.

## 2. Puntos duplicados

Se eliminan los puntos consecutivos idénticos (3 archivos, 1 punto cada uno: `e337`, `e817`, `fxlv152`). XFOIL falla con dos puntos iguales seguidos, porque generan un panel de longitud cero.

## 3. Normalización

Se transforma cada perfil para que el borde de ataque quede en (0, 0) y el de salida en (1, 0).

**Definiciones:**
- **Borde de salida (BS):** punto medio entre el primer y el último punto. Funciona tanto con bordes de salida cerrados como abiertos.
- **Borde de ataque (BA):** punto del contorno más alejado del borde de salida. Es la definición de XFOIL y, a diferencia del punto de x mínima, no depende de la orientación del perfil.

**Transformaciones, en este orden:**
1. **Trasladar** el perfil para que el BA quede en el origen.
2. **Girar** un ángulo −θ, siendo θ el ángulo de la cuerda, para que la cuerda quede horizontal.
3. **Escalar** dividiendo entre la longitud de la cuerda, para que mida 1.

Trasladar primero es necesario porque el giro y el escalado se hacen respecto al origen.

### Decisión: derrotar los perfiles

Se midió la inclinación de la cuerda en los 1.656 perfiles con `src/medir_cuerda.py`:

| \|Ángulo de la cuerda\| | Perfiles | % |
|---|---|---|
| < 0,1° | 1.424 | 86 % |
| 0,1° – 1° | 200 | 12 % |
| ≥ 1° | 32 | 2 % |

Todos los perfiles inclinados lo están hacia el mismo lado (borde de ataque más alto que el de salida), y los más inclinados son perfiles de 1910–1930: Eiffel, St. Cyr, Rhodes, Curtiss, Dayton-Wright. Probablemente se definieron tomando como eje x la tangente al intradós en lugar de la cuerda.

Se decidió **girar todos los perfiles** para que α = 0 tenga el mismo significado en todo el dataset. Sin este giro, un perfil antiguo tendría su polar desplazada 2–3° respecto a uno moderno de forma equivalente, solo por la convención de medida, y el modelo de predicción aprendería esa diferencia como si fuera aerodinámica.

### Lo que se conserva

- **Bordes de salida abiertos** (617 perfiles, el 37 %). No son errores: son la geometría real del perfil. Por ejemplo, el NACA 0012 tiene, por su propia ecuación, un espesor en el borde de salida del 0,252 % de la cuerda.
- **El número de puntos** de cada perfil (de 24 a 399). El remuestreo a un número fijo de puntos se hará más adelante, cuando lo requiera el modelo.

## 4. Formato de salida

Los perfiles limpios se guardan en `data/processed/perfiles/`, con el mismo nombre de archivo que el original y en formato Selig:

```
AG35
0.999965 0.001244
0.994706 0.001957
...
```

- Primera línea: nombre del perfil.
- Resto: pares `x y` con 6 decimales (una millonésima de cuerda), en orden Selig.

Es el mismo formato que la entrada, así que lo leen directamente tanto XFOIL como `leer_perfil`.

## 5. Validación

`src/validar_limpieza.py` comprueba cada perfil limpio y guarda una tabla resumen en `data/processed/resumen_limpieza.csv`, con una fila por perfil.

| Comprobación | Criterio | Resultado |
|---|---|---|
| Número de puntos | ≥ 20 | 24 – 399 (mediana 61) |
| x mínima | ≈ 0 | 0 en todos |
| x máxima | ≤ 1,01 | ≤ 1,005 |
| Distancia del BA al origen | ≈ 0 | 0 en todos |
| Borde de salida | ≈ (1, 0) | (1, 0) en todos |
| Puntos duplicados | 0 | 0 en todos |

"≈" significa con una tolerancia de 10⁻⁵, porque los archivos están redondeados a 6 decimales.

**Resultado: 1.656 de 1.656 perfiles válidos.**

### Observaciones

- **x máxima ligeramente mayor que 1:** en 333 perfiles algún punto queda por detrás del borde de salida, como mucho un 0,5 % de la cuerda (`hs1430`). Ocurre cuando el borde de salida es abierto y su cara no es perpendicular a la cuerda: uno de los extremos queda por detrás del punto medio. Es una consecuencia de la definición del borde de salida, no un error.
- **Morros casi verticales:** en 18 perfiles (sobre todo Eppler) hay dos puntos con x = 0 separados menos de una milésima de cuerda, y ambos están prácticamente a la misma distancia del borde de salida. Al releer los datos redondeados, el criterio "punto más alejado" puede elegir cualquiera de los dos. Por eso la validación comprueba directamente que exista un punto en (0, 0), en lugar de volver a calcular el borde de ataque.

## Cómo reproducirlo

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
python src/preparar_datos_uiuc.py   # descomprime los originales en data/raw/
python src/generar_procesados.py    # limpia y guarda en data/processed/perfiles/
python src/validar_limpieza.py      # valida y genera resumen_limpieza.csv
```