from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from bd import consultar

app = FastAPI(title="Airfoil AI", description="API de perfiles aerodinámicos")

COLUMNAS_CATALOGO = """
    archivo, nombre, familia, descripcion,
    t_max, x_t_max, f_max, x_f_max, f_min, espesor_bs, area, simetrico
"""


@app.get("/salud")
def salud():
    """Comprueba que la API funciona y que puede conectarse a la base de datos."""
    consultar("SELECT 1")
    return {"estado": "ok"}


@app.get("/familias")
def familias():
    """Devuelve las familias de perfiles con su número de perfiles, de mayor a menor."""
    return consultar(
        """
        SELECT familia, COUNT(*) AS n_perfiles
        FROM perfiles
        GROUP BY familia
        ORDER BY n_perfiles DESC
        """
    )


@app.get("/perfiles")
def perfiles(
    familia: Annotated[list[str] | None, Query()] = None,
    espesor_min: Annotated[float | None, Query(ge=0, le=1)] = None,
    espesor_max: Annotated[float | None, Query(ge=0, le=1)] = None,
    curvatura_min: Annotated[float | None, Query(ge=-1, le=1)] = None,
    curvatura_max: Annotated[float | None, Query(ge=-1, le=1)] = None,
):
    """Devuelve el catálogo de perfiles, filtrado por familia, espesor y curvatura (en fracción de cuerda)."""
    if espesor_min is not None and espesor_max is not None and espesor_min > espesor_max:
        raise HTTPException(status_code=400, detail="espesor_min no puede ser mayor que espesor_max")
    if curvatura_min is not None and curvatura_max is not None and curvatura_min > curvatura_max:
        raise HTTPException(status_code=400, detail="curvatura_min no puede ser mayor que curvatura_max")

    condiciones = []
    parametros = []

    if familia:
        condiciones.append("familia = ANY(%s)")
        parametros.append(familia)
    if espesor_min is not None:
        condiciones.append("t_max >= %s")
        parametros.append(espesor_min)
    if espesor_max is not None:
        condiciones.append("t_max <= %s")
        parametros.append(espesor_max)
    if curvatura_min is not None:
        condiciones.append("f_max >= %s")
        parametros.append(curvatura_min)
    if curvatura_max is not None:
        condiciones.append("f_max <= %s")
        parametros.append(curvatura_max)

    sql = f"SELECT {COLUMNAS_CATALOGO} FROM perfiles"
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY archivo"

    return consultar(sql, parametros)