# Formato de los archivos .dat de la UIUC

Análisis de los archivos de `data/raw/coord_seligFmt/` (versión de la base de datos del 23/02/2026, 1.665 archivos) para definir los criterios del lector y de la limpieza.

Método: primero se revisó a mano una muestra de 12 perfiles para formular hipótesis; después cada hipótesis se comprobó con un script sobre los 1.665 archivos.

## Muestra revisada a mano

| Archivo | Nº puntos | Primer punto | Último punto | BS | Observaciones |
|---|---|---|---|---|---|
| n0012.dat | 131 | (1.0, 0.00126) | (1.0, −0.00126) | abierto | No existe `naca0012.dat`: los NACA usan el prefijo `n` |
| clarky.dat | 121 | (1.0, 0.00060) | (1.0, −0.00060) | abierto | |
| e387.dat | 61 | (1.0, 0.0) | (1.0, 0.0) | cerrado | Columnas con espacios a la izquierda |
| s1223.dat | 81 | (1.0, 0.0) | (1.0, 0.0) | cerrado | |
| fx63137.dat | 97 | (1.0, 0.0) | (1.0, 0.0) | cerrado | Nombre empieza por "WORTMANN", no por "FX" |
| goe398.dat | 33 | (1.0, 0.0) | (1.0, 0.0) | cerrado | Discretización gruesa |
| b707a.dat | 121 | (1.0, 0.0) | (1.0, 0.0) | cerrado | |
| giiia.dat | 51 | (0.99998, 0.00018) | (1.0, −0.00018) | abierto | Primer punto no exactamente en x = 1 |
| vr8b.dat | 59 | (1.01, 0.0034) | (1.01, −0.0016) | abierto | x llega a 1.01 por el tab; números tipo `.96` |
| v13009.dat | 39 | (1.0, 0.00055) | (1.0, −0.00055) | abierto | 7 decimales |
| stcyr172.dat | 33 | (1.0, 0.0) | (1.0, 0.0) | cerrado | Discretización gruesa |

BS = borde de salida. BA = borde de ataque.

## Hipótesis y comprobación sobre los 1.665 archivos

| # | Hipótesis | Resultado | Casos que la incumplen |
|---|---|---|---|
| H1 | La línea 1 es el nombre; el resto son pares (x, y) | ✅ casi siempre | `30p-30n.dat` empieza con comentarios `#` en vez de nombre |
| H2 | Columnas separadas por espacios de anchura variable | ✅ | 2 usan tabuladores (`lrn1007`, `naca64a010`); `split()` lo resuelve |
| H3 | x está en [0, 1] (tolerancia 0,1 % de cuerda) | ❌ 10 archivos | Multielemento (`30p-30n*`), perfiles extendidos o con tab (`e664ex` hasta 1.2, `vr8b`), y pequeñas desviaciones (`s1221`, `t16`, `sc1095r8`…) |
| H4 | Orden Selig: BS → extradós → BA → intradós → BS | ✅ 1.660 | Orientación invertida en los 4 `30p-30n*`; `naca1.dat` no es un perfil |
| H5 | El BA está en (0, 0) (tolerancia 0,1 % de cuerda) | ❌ 221 archivos | El punto de x mínima tiene y ≠ 0, a veces de forma notable (`ag35`: y = 0,0285) |
| H6 | El BS puede estar abierto o cerrado | ✅ | Cerrado: 1.048. Abierto: 617 (mediana del espesor: 0,28 % de cuerda; 37 por encima del 1 %) |
| H7 | El número de puntos varía mucho | ✅ | De 24 (`e49`) a 664 (`30p-30n`); mediana 61 |
| H8 | Hay líneas de comentario `#` | ✅ solo 3 | `30p-30n.dat`, `s9104.dat`, `s9104BTE.dat` |
| H9 | Hay líneas vacías | ✅ 8 | Al final del archivo (`cap21c`, `s2027`, `hs1430`…) |
| H10 | Hay puntos consecutivos repetidos | ✅ 3 | `e337`, `e817`, `fxlv152` (1 duplicado cada uno) |
| H11 | Hay notación científica | ✅ 3 | `ht33`, `ht34`, `ht35`; `float()` lo lee bien |
| H12 | Codificación y saltos de línea | ✅ | Todos en UTF-8 y con saltos de línea de Windows (CRLF) |

## Casos especiales

- **`naca1.dat`** es el carenado de un motor (*NACA-1 cowl*), no un perfil: es una curva abierta que va de (1, 1) a (0, 0). Se excluye.
- **Configuraciones multielemento:** `30p-30n.dat` contiene slat, elemento principal y flap en un único archivo, separados por comentarios. Además existen los elementos por separado (`30p-30n-slat`, `-main`, `-flap`, `r1145ms*`, `ua79sf*`). XFOIL solo analiza perfiles de un elemento, así que se excluyen o se marcan.
- **BS muy grueso:** algunos perfiles de turbina eólica tienen BS de varios puntos porcentuales de cuerda (`ah93w480b`: 23 %, `fx79w660a`: 8,5 %). Son perfiles de raíz de pala, válidos pero atípicos.

## Requisitos para el lector (paso 3)

1. Primera línea → nombre (quitando espacios con `.strip()`). Si empieza por `#`, tratarla como comentario.
2. Ignorar líneas vacías y líneas que empiecen por `#`.
3. Separar columnas con `split()` y convertir con `float()`.
4. Cualquier línea que no sean dos números → registrar el archivo como problemático, no detener la lectura.
5. Devolver también avisos: duplicados consecutivos, x fuera de [0, 1], orientación invertida.

## Decisiones de limpieza que salen de los datos (paso 4)

- **Normalizar** todos los perfiles: BA en (0, 0) y cuerda unitaria. Necesario porque 221 perfiles tienen el BA desplazado y 10 se salen de [0, 1].
- **Eliminar** los puntos consecutivos duplicados (3 archivos).
- **Excluir** `naca1.dat` y los archivos multielemento.
- **Conservar** los BS abiertos (617 perfiles, el 37 %): no son errores, sino geometría real.
- **Remuestrear** a un número fijo de puntos, por la gran variación (24–664). Necesario para los modelos de IA.