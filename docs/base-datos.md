# Base de datos

Base de datos PostgreSQL con el catálogo de la Fase 1 (`data/processed/perfiles.csv`) y las coordenadas de todos los perfiles limpios (`data/processed/perfiles/*.dat`). Es la fuente de datos de la API y de la herramienta de visualización, y en la Fase 2 guardará también los resultados de XFOIL.

## Resumen

| Elemento | Archivo | Resultado |
|---|---|---|
| Servicio de PostgreSQL | `docker-compose.yml`, `.env` | PostgreSQL 17 en Docker, puerto 5432 |
| Esquema | `sql/esquema.sql` | Tablas `perfiles` y `coordenadas` |
| Carga y validación | `src/cargar_bd.py` | 1.656 perfiles y 110.767 puntos |

## 1. Arquitectura

```
data/processed/perfiles.csv  ──┐
                               ├──► src/cargar_bd.py ──► PostgreSQL (Docker)
data/processed/perfiles/*.dat ─┘                         ├── perfiles
                                                         └── coordenadas
```

### Docker

La base de datos se ejecuta en un contenedor con la imagen oficial `postgres:17`, definido en `docker-compose.yml`:

- **Credenciales en `.env`.** Usuario, contraseña y nombre de la base se leen del archivo `.env`, que **no se sube al repositorio** (está en el `.gitignore`). En el repositorio solo está `.env.example`, una plantilla con las mismas variables.
- **Puerto 5432.** El puerto del contenedor se conecta al del ordenador, para que los scripts de Python (y luego la API) se conecten a `localhost:5432`.
- **Volumen `datos_bd`.** Los datos se guardan fuera del contenedor: se conservan aunque el contenedor se pare o se borre.
- **Esquema automático.** La carpeta `sql/` se monta en `/docker-entrypoint-initdb.d`, y PostgreSQL ejecuta sus archivos `.sql` al crear la base. Así, `docker compose up -d` deja la base lista, con las tablas creadas, sin ningún paso manual.

### Por qué el esquema está en el repositorio

Las tablas se podrían crear a mano desde `psql`, pero entonces su definición solo existiría dentro de una base concreta. Con `sql/esquema.sql` en el repositorio:

- cualquiera que clone el proyecto obtiene exactamente la misma base;
- los cambios en las tablas quedan en el historial de Git;
- el propio archivo documenta la estructura de los datos;
- el despliegue (Fase 6) se puede automatizar.

## 2. Esquema

### Tabla `perfiles`

Una fila por perfil, con las mismas columnas que el catálogo (descritas en [`geometria.md`](geometria.md) y [`clasificacion.md`](clasificacion.md)).

| Columna | Tipo | Vacía | Motivo |
|---|---|---|---|
| `archivo` | `TEXT` | No | **Clave primaria** |
| `nombre` | `TEXT` | No | Cabecera del `.dat`; todos la tienen |
| `familia` | `TEXT` | No | Los perfiles sin familia van a "Otros" |
| `descripcion` | `TEXT` | **Sí** | 75 perfiles no tienen descripción en la web de la UIUC |
| `t_max`, `x_t_max`, `f_max`, `f_min`, `espesor_bs`, `area` | `DOUBLE PRECISION` | No | Se calculan para todos los perfiles |
| `x_f_max` | `DOUBLE PRECISION` | **Sí** | Vacía en los perfiles sin curvatura positiva, donde no tiene sentido físico |
| `simetrico` | `BOOLEAN` | No | Se calcula para todos los perfiles |

### Tabla `coordenadas`

Una fila por punto del contorno.

| Columna | Tipo | Descripción |
|---|---|---|
| `archivo` | `TEXT` | Perfil al que pertenece el punto. **Clave foránea** a `perfiles` |
| `orden` | `INTEGER` | Posición del punto en el contorno (0, 1, 2…), en orden Selig |
| `x`, `y` | `DOUBLE PRECISION` | Coordenadas normalizadas (x/c, y/c) |

Clave primaria: **(`archivo`, `orden`)**.

### Decisiones

- **`archivo` como clave primaria.** Es el único campo que identifica a cada perfil sin ambigüedad: viene de los nombres de archivo de una misma carpeta, así que no se repite. Es también la columna por la que se unen las tablas en `generar_catalogo.py`.
- **`NOT NULL` según los datos.** Solo pueden quedar vacías las dos columnas que tienen huecos justificados: `descripcion` y `x_f_max`. En el resto, un valor vacío sería un error de las fases anteriores, y la base lo rechaza al cargar. Funciona como una validación adicional.
- **Coordenadas en una tabla aparte.** Cada perfil tiene un número distinto de puntos (66,9 de media), así que no caben como columnas de `perfiles`. Separar las dos entidades es la normalización habitual en bases de datos relacionales.
- **Columna `orden`.** Las filas de una tabla SQL no tienen un orden garantizado, y el contorno solo tiene sentido en orden Selig (borde de salida → extradós → borde de ataque → intradós → borde de salida). Con `ORDER BY orden`, el perfil siempre se reconstruye bien.
- **Clave primaria compuesta.** Ni `archivo` ni `orden` son únicos por separado, pero la pareja sí: "el punto 37 del naca2412" solo hay uno. Además, la clave crea un índice que empieza por `archivo`, de modo que la consulta más habitual, los puntos de un perfil, es rápida.
- **Clave foránea con `ON DELETE CASCADE`.** No se pueden guardar puntos de un perfil que no existe, y al borrar un perfil se borran sus puntos.
- **`DOUBLE PRECISION`.** Son 8 bytes, el mismo tipo que el `float64` de numpy, así que no se pierde precisión entre pandas y la base. `REAL` (4 bytes) redondearía a unas 7 cifras significativas.

## 3. Carga

`src/cargar_bd.py` hace la carga completa:

1. **Lectura.** Lee `perfiles.csv` y, para cada perfil del catálogo, su archivo `.dat`. Todo se prepara en memoria antes de conectar con la base: si un archivo falla, la base no se toca.
2. **Vaciado.** `TRUNCATE perfiles CASCADE` vacía las dos tablas.
3. **Inserción.** Primero `perfiles` y después `coordenadas`, porque la clave foránea exige que el perfil exista antes que sus puntos.
4. **Validación.** Compara lo que hay en la base con lo que se ha leído.

### Decisiones

- **Idempotente.** Gracias al vaciado inicial, el script se puede ejecutar varias veces y la base siempre queda igual, como el resto de scripts, que regeneran `data/` desde cero.
- **Una sola transacción.** El vaciado y las inserciones se confirman juntos. Si algo falla a mitad (por ejemplo, un valor vacío en una columna `NOT NULL`), se deshace todo, incluido el vaciado: la base nunca queda cargada a medias.
- **Coordenadas a partir del catálogo.** Se recorren los perfiles de `perfiles.csv` y no la carpeta de `.dat`, así que nunca se intenta insertar un punto de un perfil que no está en la tabla `perfiles`.
- **NaN → `NULL`.** Para pandas, NaN significa "vacío", pero para PostgreSQL es un número válido. Los NaN se convierten en `None` (`NULL` en SQL) para que las consultas del tipo `WHERE x_f_max IS NULL` funcionen.
- **Tipos de Python.** psycopg2 no sabe guardar algunos tipos de numpy (`numpy.bool_`), así que los valores se convierten antes a `float`, `bool` y `str` de Python.
- **Inserción por lotes.** `execute_values` inserta miles de filas en cada consulta, en lugar de una consulta por fila. Con `page_size=10_000`, los 110.767 puntos se cargan en 12 lotes.
- **Credenciales del `.env`.** El script se ejecuta fuera de Docker, así que lee las credenciales del mismo `.env` con `python-dotenv`. No hay contraseñas en el código.

## 4. Validación

Al terminar la carga, el script comprueba tres cosas:

| Comprobación | Resultado |
|---|---|
| Perfiles en la base = perfiles leídos del catálogo | 1.656 = 1.656 |
| Puntos en la base = puntos leídos de los `.dat` | 110.767 = 110.767 |
| Recuento por familia en la base = recuento en el catálogo | Coinciden todas las familias |

La tercera comprobación detectaría, por ejemplo, columnas cruzadas en la inserción. Además, una segunda ejecución del script da exactamente los mismos resultados, lo que confirma que es idempotente.

## 5. Uso

```bash
cp .env.example .env               # y cambia la contraseña en .env
docker compose up -d               # levanta PostgreSQL y crea las tablas
python src/cargar_bd.py            # carga y valida
docker compose down                # para la base sin borrar los datos
```

Consultas de ejemplo desde `psql`:

```bash
docker compose exec db psql -U airfoil -d airfoil -c "SELECT familia, COUNT(*) FROM perfiles GROUP BY familia ORDER BY 2 DESC"
docker compose exec db psql -U airfoil -d airfoil -c "SELECT x, y FROM coordenadas WHERE archivo = 'naca2412.dat' ORDER BY orden"
```

## 6. Limitaciones y pasos futuros

- **El esquema solo se aplica al crear la base.** PostgreSQL ejecuta `sql/` únicamente cuando el volumen está vacío. Si se cambia `esquema.sql`, hay que borrar el volumen y volver a cargar: `docker compose down -v`, `docker compose up -d` y `python src/cargar_bd.py`. Mientras todos los datos se puedan regenerar con scripts, es suficiente.
- **Migraciones.** Cuando la base guarde datos costosos de regenerar, como las polares de XFOIL de la Fase 2, los cambios de esquema se harán con migraciones (archivos numerados que modifican una base existente) en lugar de borrarla.
- **Puerto 5432 ocupado.** Si ya hay otro PostgreSQL en el ordenador, el contenedor no arranca. Basta con cambiar el puerto del ordenador en `docker-compose.yml` (por ejemplo, `"5433:5432"`) y el del script.