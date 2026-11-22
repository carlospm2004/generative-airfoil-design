# API

API con FastAPI que da acceso a los datos de la base de datos ([`base-datos.md`](base-datos.md)): catálogo de perfiles con filtros, ficha de cada perfil y coordenadas de su contorno. Es la capa intermedia entre la base de datos y la interfaz web, y en las siguientes fases servirá también las polares de XFOIL, el modelo de predicción y el diseño de perfiles.

## Resumen

| Elemento | Archivo | Descripción |
|---|---|---|
| Endpoints | `api/main.py` | Aplicación FastAPI |
| Acceso a la base | `api/bd.py` | Función `consultar` |
| Imagen de Docker | `api/Dockerfile`, `api/.dockerignore`, `api/requirements.txt` | La API como servicio de `docker compose` |

## 1. Arquitectura

```
Navegador (frontend) ──HTTP/JSON──► API (FastAPI) ──SQL──► PostgreSQL
                                     contenedor "api"       contenedor "db"
                                     puerto 8000            puerto 5432
```

El frontend nunca habla directamente con la base de datos:

- **Un navegador no puede conectarse a PostgreSQL**: solo hace peticiones HTTP.
- **Seguridad.** Las credenciales de la base se quedan en el servidor, y el usuario solo puede hacer las consultas que define la API.
- **La lógica está en un único sitio**: consultas, validaciones y formatos de respuesta.
- **Las piezas son independientes.** Se puede cambiar el frontend o la base sin tocar el resto, mientras se mantengan los endpoints.

La API está en `api/` y no en `src/` porque es un tipo de código distinto: `src/` contiene **scripts** que se ejecutan una vez y terminan, y `api/` es un **servicio** que se queda en marcha atendiendo peticiones, con su propia imagen de Docker.

## 2. Endpoints

| Método y ruta | Parámetros | Devuelve |
|---|---|---|
| `GET /salud` | — | `{"estado": "ok"}` si la API llega a la base de datos |
| `GET /familias` | — | Familias con su número de perfiles, de mayor a menor |
| `GET /perfiles` | `familia` (repetible), `espesor_min`, `espesor_max`, `curvatura_min`, `curvatura_max` | Catálogo de perfiles que cumplen los filtros, ordenado por archivo |
| `GET /perfiles/{archivo}` | `archivo` en la ruta | Datos de un perfil |
| `GET /perfiles/{archivo}/coordenadas` | `archivo` en la ruta | `{"archivo", "x": [...], "y": [...]}` en orden Selig |

La documentación interactiva, generada por FastAPI, está en `http://localhost:8000/docs`.

### Ejemplos

```
GET /perfiles?familia=NACA&familia=E&espesor_min=0.10&espesor_max=0.15
GET /perfiles/naca2412.dat
GET /perfiles/naca2412.dat/coordenadas
```

### Códigos de respuesta

| Código | Cuándo |
|---|---|
| 200 | Petición correcta |
| 400 | Rango imposible: `espesor_min > espesor_max` o `curvatura_min > curvatura_max` |
| 404 | El perfil no existe |
| 422 | Parámetro fuera de rango o con formato inválido (por ejemplo, `espesor_max=2`) |
| 500 | Error del servidor; por ejemplo, la base de datos no responde |

## 3. Decisiones

### Acceso a la base de datos

- **Una sola función, `consultar(sql, parametros)`.** Todos los endpoints conectan, ejecutan un `SELECT` y devuelven filas, así que eso está en un único sitio. Para cambiar la forma de conectar, se toca solo esa función.
- **`RealDictCursor`.** Las filas se devuelven como diccionarios con los nombres de las columnas, que FastAPI convierte directamente en JSON.
- **La conexión se cierra siempre** (`try / finally`). La API está en marcha continuamente: si no se cerraran, se acumularían conexiones abiertas hasta superar el límite de PostgreSQL (100 por defecto).
- **Host configurable** (`POSTGRES_HOST`). Vale `localhost` cuando la API se ejecuta en el ordenador y `db` cuando se ejecuta en Docker, donde cada servicio de compose se encuentra por su nombre. El código es el mismo en los dos casos.

### Seguridad: inyección SQL

Los valores que manda el usuario **nunca se pegan en el texto del SQL**: se pasan siempre como parámetros (`%s`), y psycopg2 los escapa. En el SQL solo se insertan textos escritos en el propio código (nombres de columna y condiciones). Comprobado: con `?familia=x';DROP TABLE perfiles;--`, la API busca una familia con ese nombre literal, devuelve una lista vacía y la tabla sigue intacta.

### `/salud`

Ejecuta `SELECT 1`, la consulta más ligera posible: no lee ninguna tabla. Comprueba que la base está levantada, que las credenciales funcionan y que responde. Si algo falla, la API responde con un error 500. Es el endpoint que Docker o la nube usarán para saber si el servicio está vivo.

### `/familias`

El recuento se hace en SQL (`GROUP BY`) y no en Python: viajan unas 26 filas en lugar de 1.656. La lista de familias sale de los datos, así que una familia nueva aparece sola en el frontend.

### `/perfiles`

- **Filtros opcionales**: solo se aplican los que se envían. El `WHERE` se construye añadiendo, para cada filtro, una condición y su valor, en el mismo orden.
- **Nombres de los parámetros**: `espesor_min` y `espesor_max` en lugar de `t_max_min`, para no confundir los límites del filtro con la columna `t_max`.
- **Unidades: fracción de cuerda**, las mismas que la base de datos (`espesor_max=0.15` es un 15 %). La conversión a porcentaje se hace en el frontend.
- **Validación automática** con `Query(ge=..., le=...)`: el espesor tiene que estar entre 0 y 1, y la curvatura entre −1 y 1, porque existen perfiles con curvatura negativa. Los rangos con mínimo mayor que máximo se comprueban en el código y devuelven un error 400 con un mensaje, en lugar de una lista vacía que no explicaría el problema.
- **Varias familias**: `?familia=NACA&familia=E`. En SQL, `familia = ANY(%s)` sirve para cualquier número de familias.
- **`ORDER BY archivo`**: la misma petición devuelve siempre el mismo orden.

### Ficha y coordenadas

- **Rutas REST**: `/perfiles` es la colección, `/perfiles/{archivo}` un elemento y `/perfiles/{archivo}/coordenadas` algo que le pertenece.
- **404 si el perfil no existe**, en lugar de un error 500. En las coordenadas, "sin puntos" equivale a "no existe": la carga validó que los 1.656 perfiles tienen sus puntos.
- **Coordenadas como dos listas**, `x` e `y`, en lugar de una lista de puntos `{"x", "y"}`. Es el formato que usan las librerías de gráficos, y la respuesta ocupa aproximadamente la mitad.

## 4. Docker

### Imagen

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["fastapi", "run", "main.py", "--port", "8000"]
```

- **Dependencias propias** (`api/requirements.txt`): solo FastAPI, psycopg2 y python-dotenv. Sin numpy ni pandas, la imagen es más ligera y se construye y despliega más rápido.
- **Primero las dependencias y después el código.** Docker guarda cada paso en caché: si solo cambia el código, no se vuelven a instalar las librerías.
- **`fastapi run`** (modo producción) en lugar de `fastapi dev`: escucha en `0.0.0.0`, así que acepta conexiones desde fuera del contenedor.
- **`.dockerignore`** excluye `__pycache__/` y `.env`. Las contraseñas no van dentro de la imagen: `docker compose` las pasa como variables de entorno al arrancar el contenedor.

### `docker compose`

- El servicio `api` se construye con `build: ./api` y se conecta a la base con `POSTGRES_HOST: db`.
- El servicio `db` tiene un `healthcheck` con `pg_isready`, y la API solo arranca cuando la base está lista (`depends_on` con `condition: service_healthy`). Así no intenta conectarse mientras PostgreSQL se inicia.

## 5. Uso

Con Docker (la forma habitual):

```bash
docker compose up -d --build       # base de datos y API
docker compose ps                  # db: healthy, api: running
docker compose logs api            # si la API no arranca
```

En desarrollo, con recarga automática al guardar (parando antes el contenedor de la API con `docker compose stop api`):

```bash
fastapi dev api/main.py
```

## 6. Comprobaciones

| Petición | Resultado esperado |
|---|---|
| `/salud` | `{"estado": "ok"}`; error 500 con la base parada |
| `/familias` | 26 entradas (25 familias y Otros), empezando por Historico (402); suma 1.656 |
| `/perfiles` | 1.656 perfiles |
| `/perfiles?familia=NACA` | 170 perfiles |
| `/perfiles?familia=NACA&familia=E` | 370 perfiles |
| `/perfiles?espesor_min=0.2&espesor_max=0.1` | Error 400 |
| `/perfiles?espesor_max=2` | Error 422 |
| `/perfiles/n0012.dat` | `simetrico: true`, `x_f_max: null` |
| `/perfiles/naca2412.dat/coordenadas` | `x` e `y` de la misma longitud; `x` empieza en 1, baja a 0 y vuelve a 1 |
| `/perfiles/noexiste.dat` | Error 404 |

## 7. Limitaciones y pasos futuros

- **Una conexión por petición.** Abrir una conexión cuesta unos milisegundos. Con un solo usuario es suficiente; si la API recibe muchas peticiones (Fase 6), se usará un *pool* de conexiones reutilizables, cambiando solo `consultar`.
- **Sin paginación.** `/perfiles` devuelve todos los resultados de una vez. Con 1.656 perfiles no es un problema; con las polares de la Fase 2, que serán muchas más filas, habrá que paginar o filtrar siempre por perfil y Reynolds.
- **CORS.** Cuando la interfaz web se sirva desde otro origen (otro puerto), el navegador bloqueará sus peticiones a la API si esta no lo permite expresamente. Se configurará al crear el frontend.
- **Sin autenticación.** La API es de solo lectura y local. Antes del despliegue público habrá que valorar si alguna parte necesita protección.