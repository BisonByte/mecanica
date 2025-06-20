import argparse
from beam import Viga, calcular_reacciones_viga, centro_de_masa_viga


def main() -> None:
    parser = argparse.ArgumentParser(description="Herramientas de cálculo de vigas")
    sub = parser.add_subparsers(dest="cmd")

    p_reacc = sub.add_parser("reacciones", help="Calcular reacciones de una viga")
    p_reacc.add_argument("--longitud", type=float, required=True)
    p_reacc.add_argument("--par", type=float, default=0.0)
    p_reacc.add_argument("--apoyo-c", type=float, dest="apoyo_c")
    p_reacc.add_argument("--carga", nargs=2, action="append", metavar=("POS", "MAG"), type=float, default=[])
    p_reacc.add_argument("--dist", nargs=3, action="append", metavar=("INI", "FIN", "MAG"), type=float, default=[])

    p_cm = sub.add_parser("centro_masa", help="Calcular centro de masa de las cargas")
    p_cm.add_argument("--longitud", type=float, required=True)
    p_cm.add_argument("--carga", nargs=2, action="append", metavar=("POS", "MAG"), type=float, default=[])
    p_cm.add_argument("--dist", nargs=3, action="append", metavar=("INI", "FIN", "MAG"), type=float, default=[])

    args = parser.parse_args()

    if args.cmd == "reacciones":
        viga = Viga(longitud=args.longitud)
        if args.apoyo_c is not None:
            viga.tipo_apoyo_c = "Fijo"
            viga.posicion_apoyo_c = args.apoyo_c
        viga.par_torsor = args.par
        for pos, mag in args.carga:
            viga.agregar_carga_puntual(pos, mag)
        for ini, fin, mag in args.dist:
            viga.agregar_carga_distribuida(ini, fin, mag)
        ra, rb, rc = calcular_reacciones_viga(viga)
        print(f"RA={ra:.2f} RB={rb:.2f} RC={rc:.2f}")
    elif args.cmd == "centro_masa":
        viga = Viga(longitud=args.longitud)
        for pos, mag in args.carga:
            viga.agregar_carga_puntual(pos, mag)
        for ini, fin, mag in args.dist:
            viga.agregar_carga_distribuida(ini, fin, mag)
        cm = centro_de_masa_viga(viga)
        print(f"Centro de masa: {cm:.2f} m")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
