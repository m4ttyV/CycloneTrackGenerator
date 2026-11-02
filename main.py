from functions import *
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Программа для анализа данных скорости ветра в файлах NetCDF.")
    parser.add_argument(
        "--startdate", "-sd",
        required=False,
        default="2025-01-01",
        # required=True,
        help="Дата начала периода в формате yyyy-mm-dd",
    )
    parser.add_argument(
        "--period", "-p",
        required=False,
        default=0,
        help="Тип периода (0 - месяц, 1 - декада",
        type=int
    )
    parser.add_argument(
        "--cyclone", "-zn",
        required=False,
        type=int,
        default=1,
        help="Нужен ли циклон (1 или 0)",
    )
    parser.add_argument(
        "--anticyclone", "-az",
        required=False,
        type = int,
        default=1,
        help="Нужен ли антициклон (1 или 0)"
    )
    parser.add_argument(
        "--tropicalcyclone", "-tc",
        required=False,
        type=int,
        default=0,
        help="Нужен ли тропический циклон (1 или 0)"
    )
    parser.add_argument(
        "--pathtosave", "-pts",
        required=False,
        default="D:/tmp/test2506/",
        help="Путь куда сохранять"
    )
    parser.add_argument(
        "--dots_slp", "-slp",
        required=False,
        type=float,
        default=0,
        help="Нужно ли давление точек"
    )
    parser.add_argument(
        "--track_name", "-tn",
        required=False,
        type=int,
        default=1,
        help="Нужны ли имена линий"
    )
    parser.add_argument(
        "--blanc_type", "-bt",
        required=False,
        type=str,
        default="None",
        help="Тип бланка"
    )
    parser.add_argument(
        '-smb', '--samba_store',
        action='store_true',
        help='Нужна ли запись на smb'
    )
    parser.add_argument(
        '-sf', '--save_fig',
        action='store_true',
        help='Нужно ли сохранять изображения'
    )
    # Передаем аргументы
    args = parser.parse_args()
    cis_type_zn = True
    cis_type_az = True
    cis_type_tc = True
    is_slp = True
    is_track_name = True
    blanc_type = args.blanc_type

    if args.cyclone == 0:
        cis_type_zn = False

    if args.anticyclone == 0:
        cis_type_az = False

    if args.tropicalcyclone == 0: 
        cis_type_tc = False

    if args.dots_slp == 0:
        is_slp = False

    if args.track_name == 0:
        is_track_name = False

    main(cis_type_zn, cis_type_az, cis_type_tc, args.startdate, args.period, args.pathtosave, is_slp, is_track_name, blanc_type, is_smb=args.samba_store, is_save_fig=args.save_fig)

