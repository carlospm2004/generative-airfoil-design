# Características geométricas de los perfiles

Cálculo de las características geométricas de los 1.656 perfiles limpios (`data/processed/perfiles/`) y su validación. El resultado es una tabla con una fila por perfil: `data/processed/geometria.csv`.

El proceso de limpieza previo, que deja todos los perfiles con el borde de ataque en (0, 0) y el de salida en (1, 0), está en [`limpieza.md`](limpieza.md).

## Resumen

| Etapa | Resultado | Script |
|---|---|---|
| Características por perfil | 7 por perfil | `geometria.py` |
| Tabla de geometría | 1.656 perfiles, 125 simétricos | `calcular_geometria.py` |
| Validación con los NACA de 4 cifras | 26 de 28 correctos, 0 fallos inesperados | `validar_geometria.py` |

## 1. Características

Todas se expresan como fracción de la cuerda (c = 1); el área, en c².

| Columna | Característica | Descripción |
|---|---|---|
| `t_max` | Espesor máximo (t/c) | Mayor distancia vertical entre extradós e intradós |
| `x_t_max` | Posición del espesor máximo | Coordenada x donde se alcanza `t_max` |
| `f_max` | Curvatura máxima (f/c) | Mayor separación de la línea media por encima de la cuerda |
| `x_f_max` | Posición de la curvatura máxima | Coordenada x donde se alcanza `f_max`. Vacía si no hay curvatura positiva |
| `f_min` | Curvatura mínima | Punto más bajo de la línea media. Negativo en perfiles *reflex* o de curvatura negativa |
| `espesor_bs` | Espesor del borde de salida | Distancia entre el primer y el último punto del contorno. 0 si el borde de salida está cerrado |
| `area` | Área de la sección (A/c²) | Área encerrada por el contorno |
| `simetrico` | Perfil simétrico | `True` si la línea media no se separa de la cuerda más de 10⁻⁴ en ningún sentido |

## 2. Método

1. **Separar las superficies.** En orden Selig, el borde de ataque, el punto en (0, 0), divide el contorno en extradós e intradós. Las dos superficies se ordenan de x = 0 a x = 1.
2. **Interpolar en una rejilla común.** Los puntos del extradós y del intradós no suelen estar en las mismas x, así que ambas superficies se interpolan linealmente (`np.interp`) en una rejilla de 201 puntos entre 0 y 1, con un paso de 0,005.
3. **Espesor y línea media** en cada x de la rejilla:
   - espesor: t(x) = y_extradós(x) − y_intradós(x);
   - línea media: y_c(x) = [y_extradós(x) + y_intradós(x)] / 2.
4. **Máximos y posiciones:** `t_max` y `f_max` son los máximos de cada curva, y `x_t_max` y `x_f_max`, las x donde se alcanzan. `f_min` es el mínimo de la línea media.
5. **Área:** integral del espesor a lo largo de la cuerda, A = ∫₀¹ t(x) dx, con la regla del trapecio. Se comprobó con la fórmula del área de un polígono aplicada directamente al contorno: la diferencia es menor de 10⁻⁴.

**Convención de medida:** el espesor se mide en vertical, a x constante. En la definición de los perfiles NACA, el espesor se aplica perpendicular a la línea media. La diferencia es inapreciable en perfiles poco curvados y crece con la curvatura (0,03 % de cuerda en la curvatura de un NACA 6412). Es la convención habitual para comparar perfiles en un dataset.

## 3. Decisiones

### Curvatura mínima (`f_min`)

Con solo `f_max`, un perfil con la línea media por debajo de la cuerda parecería simétrico. En 28 perfiles la línea media baja más de un 0,5 % de cuerda; por ejemplo:

- `zv15_35`: `f_max` = 0 y `f_min` = −1,1 %. Sin `f_min` se clasificaría como simétrico.
- `ht08`, `ht13`, `ht14`…: perfiles de Drela para estabilizador horizontal, casi simétricos y con una ligera curvatura negativa.
- `prandtl-d-wingtip`: punta del ala volante Prandtl-D, con curvatura negativa.

`f_min` es además relevante para alas volantes, porque está relacionada con el momento de cabeceo del perfil.

### Umbral de simetría

Se midió la mayor separación de la línea media respecto de la cuerda, en valor absoluto, en los 1.656 perfiles:

| \|Curvatura\| máxima | Perfiles |
|---|---|---|
| < 10⁻⁵ (0,001 % de cuerda) | 123 |
| < 10⁻⁴ (0,01 %) | 125 |
| < 5·10⁻⁴ (0,05 %) | 132 |
| < 10⁻³ (0,1 %) | 144 |

123 perfiles son exactamente simétricos y 2 más quedan por debajo de 10⁻⁴; a partir de ahí el recuento crece de forma gradual. Se fija el umbral en **10⁻⁴**: **125 perfiles simétricos**. En una cuerda de 30 cm, equivale a 0,03 mm.

Un perfil es simétrico si `f_max` < 10⁻⁴ **y** `f_min` > −10⁻⁴.

### Posición de la curvatura vacía

En los perfiles sin curvatura positiva (`f_max` < 10⁻⁴) la posición de la curvatura máxima no tiene significado físico, así que `x_f_max` se deja vacía (`NaN`) en lugar de 0. Afecta a 142 perfiles: los 125 simétricos y 17 con curvatura solo negativa. Un 0 sería un valor engañoso y desplazaría las estadísticas; pandas ignora los `NaN` al calcularlas.

## 4. Validación con los NACA de 4 cifras

Los NACA de 4 cifras llevan su geometría en el nombre: en el NACA **MPXX**, la curvatura máxima es M % de la cuerda, está en la posición P/10 y el espesor es XX %. `validar_geometria.py` reconoce estos perfiles por el nombre del archivo (`naca2412.dat`, `n0012.dat`…), calcula los valores teóricos y los compara con los calculados.

**Tolerancias:** 0,2 % de cuerda en espesor y curvatura y 2 % en la posición de la curvatura. Cubren el paso de la rejilla (0,5 %) y la diferencia de convención de medida.

**Resultado:** 28 perfiles NACA de 4 cifras; **26 correctos**. Sin contar las excepciones, los errores máximos son:

| | Error máximo |
|---|---|
| Espesor máximo | 0,04 % de cuerda |
| Curvatura máxima | 0,04 % de cuerda |
| Posición de la curvatura | 0,5 % de cuerda (el paso de la rejilla) |

### Excepciones: errores en los datos de origen

Los dos perfiles que no cumplen se analizaron generando su geometría con la ecuación exacta de los NACA de 4 cifras. Con esa geometría teórica, el método da los valores correctos, así que los fallos se deben a los archivos de la UIUC:

| Archivo | Problema |
|---|---|
| `naca2411.dat` | La cabecera del archivo dice **NACA 2.5411**: la curvatura es del 2,5 %, no del 2 %. El nombre del archivo está recortado. El cálculo da 2,50 %, que es el valor correcto |
| `naca1410.dat` | Las coordenadas no siguen exactamente la ecuación NACA: la línea media es casi plana entre 0,3c y 0,5c (0,94 %, 0,95 % y 0,97 %) y el máximo cae en 0,5c en lugar de 0,4c. La curvatura máxima (0,97 %) sí está dentro de la tolerancia |

Se registran como excepciones conocidas en el propio script, sin relajar las tolerancias. Cualquier otro fallo se informaría como "fallo inesperado".

## 5. Resultados

| | Mínimo | Mediana | Máximo |
|---|---|---|---|
| `t_max` | 0,020 | 0,119 | 0,664 |
| `x_t_max` | 0,005 | 0,300 | 0,600 |
| `f_max` | 0 | 0,032 | 0,147 |
| `x_f_max` | 0,005 | 0,400 | 0,995 |
| `f_min` | −0,013 | 0 | 0 |
| `espesor_bs` | 0 | 0 | 0,234 |
| `area` | 0,006 | 0,078 | 0,523 |

El perfil mediano del dataset tiene un 12 % de espesor en el 30 % de la cuerda y un 3 % de curvatura en el 40 %, muy parecido a un NACA 3412. La mitad de los perfiles tiene el borde de salida cerrado.

Los extremos son geometrías reales: el espesor máximo es el `fx79w660a` (66 %), un perfil de raíz de pala eólica, y el mínimo el `sc20402` (2 %), un perfil supercrítico de la NASA.

## 6. Limitaciones conocidas

- **Placas curvadas:** en 11 perfiles el espesor máximo está antes del 10 % de la cuerda. Son placas curvadas de espesor casi constante, como el perfil del Wright Flyer de 1903 (`eiffel10`, con `x_t_max` = 0,005) o el `goe417a` (*gewölbte Platte*). En ellos el máximo puede caer en cualquier punto, y `x_t_max` es poco representativo.
- **Posición de la curvatura en perfiles poco curvados:** con curvaturas pequeñas y una línea media plana, diferencias de milésimas desplazan el máximo (caso de `naca1410`). `x_f_max` debe interpretarse con cuidado cuando `f_max` es menor de un 1 %.
- **Cruce de superficies en el borde de salida:** en 5 perfiles (`dsma523a`, `fx62k131`, `fx63147`, `ste87391`, `stf86361`) el espesor interpolado sale ligeramente negativo cerca del borde de salida, como mucho −0,05 % de cuerda. Son bordes de salida muy afilados donde las superficies se cruzan mínimamente. No afecta a ninguna característica.

## Cómo reproducirlo

Desde la raíz del repositorio, con el entorno virtual activado y los perfiles limpios generados (ver [`limpieza.md`](limpieza.md)):

```bash
python src/calcular_geometria.py    # genera data/processed/geometria.csv
python src/validar_geometria.py     # valida con los NACA de 4 cifras
```