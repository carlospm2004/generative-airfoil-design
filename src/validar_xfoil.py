# Validación de XFOIL con los perfiles NACA 0012 y 2412.

from polares import caracteristicas_polar
from xfoil import calcular_polar

# Valores de la teoría del perfil delgado
PENDIENTE_TEORICA = 0.110        # 2*pi por radián, en 1/grado
CASOS = [
    # archivo,       alfa_l0 teórico, cm teórico
    ("n0012.dat",     0.00,            0.000),
    ("naca2412.dat", -2.08,           -0.053),
]
REYNOLDS = [3e6, 6e6, 9e6]

# Tolerancias: XFOIL es viscoso y la teoría no; se admite esta diferencia
TOL_PENDIENTE = 0.10             # ±10 %
TOL_ALFA_L0 = 0.5                # ±0,5 grados
TOL_CM = 0.015

if __name__ == "__main__":
    fallos = 0
    print(f"{'Perfil':13s} {'Re':>6s} {'pts':>4s} {'dCL/da':>7s} {'a_L0':>6s} {'CM0':>7s} {'CDmin':>8s} {'CLmax':>6s} {'a':>5s}  Teoría")
    for archivo, alfa_teorico, cm_teorico in CASOS:
        for reynolds in REYNOLDS:
            estado, polar, segundos = calcular_polar(archivo, reynolds)
            if estado != "ok":
                print(f"{archivo:13s} {reynolds:6.0e}  {estado}")
                fallos += 1
                continue
            c = caracteristicas_polar(polar)
            correcto = (
                abs(c["pendiente"] / PENDIENTE_TEORICA - 1) <= TOL_PENDIENTE
                and abs(c["alfa_l0"] - alfa_teorico) <= TOL_ALFA_L0
                and abs(c["cm0"] - cm_teorico) <= TOL_CM
            )
            fallos += not correcto
            limite = "*" if c["cl_max_en_limite"] else " "
            print(
                f"{archivo:13s} {reynolds:6.0e} {len(polar):4d} {c['pendiente']:7.4f} {c['alfa_l0']:6.2f} "
                f"{c['cm0']:7.4f} {c['cd_min']:8.5f} {c['cl_max']:6.3f}{limite}{c['alfa_cl_max']:5.1f}  "
                f"{'OK' if correcto else 'FUERA DE TOLERANCIA'}"
            )
    print("\n* CL máximo en el último ángulo calculado: la pérdida no se alcanza en el rango.")
    print(f"Casos fuera de tolerancia: {fallos}")