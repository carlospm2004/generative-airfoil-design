# Interfaz web

Interfaz web para explorar los perfiles: catálogo con filtros, ficha de cada perfil, comparador y mapa del dataset. Obtiene todos los datos de la API ([`api.md`](api.md)) y no accede nunca a la base de datos.

## Resumen

| Elemento | Archivo | Descripción |
|---|---|---|
| Página | `frontend/web/index.html` | Estructura de las cuatro vistas |
| Estilos | `frontend/web/estilos.css` | Diseño visual, adaptado a móvil |
| Lógica | `frontend/web/app.js` | Peticiones a la API, navegación y gráficos |
| Servidor | `frontend/nginx.conf`, `frontend/Dockerfile` | nginx sirve la web y reenvía `/api` a la API |

## 1. Vistas

| Vista | Dirección | Qué muestra | Endpoints |
|---|---|---|---|
| Catálogo | `#/catalogo` | Tabla de perfiles con filtros por familia, espesor y curvatura, búsqueda por nombre y orden por columnas | `/familias`, `/perfiles` |
| Ficha | `#/perfil/<archivo>` | Forma del perfil con su línea media, la cota del espesor máximo y la curvatura máxima, más sus características | `/perfiles/{archivo}`, `/perfiles/{archivo}/coordenadas` |
| Comparador | `#/comparar` | Hasta 5 perfiles superpuestos y una tabla con sus características | `/perfiles`, `/perfiles/{archivo}`, `/perfiles/{archivo}/coordenadas` |
| Mapa | `#/mapa` | Un punto por perfil, curvatura máxima frente a espesor máximo, con una familia destacada. Al pulsar un punto se abre su ficha | `/perfiles`, `/familias` |

Cada vista tiene su propia dirección, así que se puede guardar o compartir el enlace a la ficha de un perfil.

## 2. Arquitectura

```
Navegador ──► nginx (contenedor "frontend", puerto 8080)
                ├── /         → archivos de frontend/web/
                └── /api/...  → API (contenedor "api", puerto 8000)
```

- **HTML, CSS y JavaScript sin frameworks.** No hace falta compilar nada: los archivos se sirven tal cual. Si en el futuro se quiere pasar a un framework (por ejemplo, React), la API no cambia.
- **Gráficos con Plotly**, cargado desde un CDN. Permite zoom, desplazamiento y ver los valores al pasar el ratón.
- **nginx como servidor y como intermediario (proxy).** El navegador pide todo al mismo origen (`localhost:8080`): la web en `/` y los datos en `/api/...`, que nginx reenvía al servicio `api`. Como para el navegador todo viene del mismo sitio, **no hace falta configurar CORS** en la API, y la dirección interna de la API no aparece en el código del frontend.
- **Unidades.** La API trabaja en fracción de cuerda; la interfaz muestra y pide los valores en porcentaje, y hace la conversión.

## 3. Decisiones

- **Línea media calculada en el navegador.** La ficha separa extradós e intradós por el borde de ataque e interpola las dos superficies en una rejilla de 201 puntos, con el mismo método que `src/geometria.py`. Así se dibuja la línea media sin añadir otro endpoint.
- **Comparador guardado en el navegador** (`localStorage`). La selección se mantiene al cambiar de vista o recargar la página. Es una preferencia de cada usuario, por lo que no se guarda en la base de datos.
- **Catálogo completo en memoria.** El comparador y el mapa piden `/perfiles` una sola vez y lo reutilizan: son 1.656 filas, una respuesta pequeña.
- **Búsqueda y orden en el navegador; filtros en la API.** Los filtros numéricos y de familia los resuelve la base de datos. La búsqueda por nombre y el orden de la tabla se hacen sobre el resultado, sin nuevas peticiones.
- **Mensajes de error útiles.** Si la API no responde, si un perfil no existe o si los filtros no devuelven nada, la interfaz dice qué ha pasado y qué hacer.
- **Accesibilidad.** Navegación con teclado, foco visible, textos alternativos en los gráficos y diseño adaptado a pantallas estrechas.
- **Seguridad.** Los textos que vienen de los datos (nombres, descripciones) se insertan como texto, nunca como HTML.

## 4. Uso

```bash
docker compose up -d --build       # base de datos, API e interfaz web
```

La interfaz queda en [`http://localhost:8080`](http://localhost:8080). Después de cambiar algún archivo de `frontend/`, hay que reconstruir la imagen con `docker compose up -d --build frontend`.

## 5. Comprobaciones

| Prueba | Resultado esperado |
|---|---|
| Abrir el catálogo | 1.656 perfiles de 1.656, y la lista de familias con sus recuentos |
| Marcar NACA | 170 perfiles |
| Abrir `#/perfil/naca2412.dat` | Perfil con curvatura, cota t = 12,0 % y curvatura máxima cerca del 2 % en x ≈ 40 % |
| Abrir `#/perfil/n0012.dat` | Línea media sobre la cuerda; curvatura máxima "sin curvatura positiva" |
| Abrir `#/perfil/noexiste.dat` | "Perfil no encontrado" con el mensaje de la API |
| Añadir 5 perfiles al comparador | Los 5 superpuestos; el sexto se rechaza con un aviso |
| Mapa con una familia destacada | Sus perfiles en naranja; al pulsar uno se abre su ficha |

## 6. Limitaciones y pasos futuros

- **Plotly y la tipografía se cargan de internet.** Sin conexión, la interfaz funciona, pero sin gráficos y con una tipografía del sistema.
- **El mapa usa dos variables** (espesor y curvatura). Cuando se vean en clase técnicas de reducción de dimensiones, como PCA, se podrá construir un mapa a partir de la forma completa de cada perfil.
- **Polares.** En la Fase 2 se añadirán a la ficha las curvas de rendimiento calculadas con XFOIL.
