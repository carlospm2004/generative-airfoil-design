# Estudio de convergencia de malla: ¿cambian los resultados al aumentar el número de paneles?

from polares import caracteristicas_polar
from xfoil import calcular_polar

CASOS = [("n0012.dat", 6e6), ("naca2412.dat", 3e6), ("naca2412.dat", 1e5)]
PANELES = [120, 160, 240, 320]

if __name__ == "__main__":
    print(f"{'Perfil':13s} {'Re':>6s} {'N':>4s} {'s':>5s} {'pts':>4s} {'dCL/da':>7s} {'CDmin':>8s} {'CLmax':>6s} {'a':>5s}")
    for archivo, reynolds in CASOS:
        for n in PANELES:
            estado, polar, segundos = calcular_polar(archivo, reynolds, n_paneles=n)
            if estado != "ok":
                print(f"{archivo:13s} {reynolds:6.0e} {n:4d}  {estado}")
                continue
            c = caracteristicas_polar(polar)
            print(f"{archivo:13s} {reynolds:6.0e} {n:4d} {segundos:5.1f} {len(polar):4d} "
                  f"{c['pendiente']:7.4f} {c['cd_min']:8.5f} {c['cl_max']:6.3f} {c['alfa_cl_max']:5.1f}")
        print()