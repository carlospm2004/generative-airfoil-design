from fastapi import FastAPI

from bd import consultar

app = FastAPI(title="Airfoil AI", description="API de perfiles aerodinámicos")


@app.get("/salud")
def salud():
    """Comprueba que la API funciona y que puede conectarse a la base de datos."""
    consultar("SELECT 1")
    return {"estado": "ok"}