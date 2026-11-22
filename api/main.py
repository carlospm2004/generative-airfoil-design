from fastapi import FastAPI

from bd import consultar

app = FastAPI(title="Airfoil AI", description="API de perfiles aerodinámicos")


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