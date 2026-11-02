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
        help="Тип периода (0 - месяц, -1 - декада, любое положительное число - период в днях",
        type=int
    )
    parser.add_argument(
        "--cyclone", "-zn",
        action="store_true",
        default=False,
        help="Нужен ли циклон",
    )
    parser.add_argument(
        "--anticyclone", "-az",
        action="store_true",
        default=False,
        help="Нужен ли антициклон"
    )
    parser.add_argument(
        "--tropicalcyclone", "-tc",
        action="store_true",
        default=False,
        help="Нужен ли тропический циклон"
    )
    parser.add_argument(
        "--pathtosave", "-pts",
        required=False,
        default="./output",
        help="Путь куда сохранять"
    )
    parser.add_argument(
        "--dots_slp", "-slp",
        action='store_true',
        default=False,
        help="Нужно ли давление точек"
    )
    parser.add_argument(
        "--track_name", "-tn",
        action='store_true',
        default=False,
        help="Нужны ли имена линий"
    )
    parser.add_argument(
        "--blanc_type_TC", "-bt",
        action='store_true',
        default=False,
        help="Тип бланка"
    )
    parser.add_argument(
        '--no_samba_store',
        action='store_false',
        default=False,
        help='Отключить запись на smb'
    )
    parser.add_argument(
        '--no_save_fig',
        action='store_false',
        default=False,
        help='Не сохранять изображения'
    )
    parser.add_argument(
        "--no_save_csv",
        action="store_false",
        default=True,
        help="Не создавать CSV-файлы",
    )
    parser.set_defaults(save_csv=True)

    args = parser.parse_args()
    main(args.cyclone, args.anticyclone, args.tropicalcyclone, args.startdate, args.period, args.pathtosave,
         args.dots_slp, args.track_name, args.blanc_type, is_smb=args.samba_store, is_save_fig=args.save_fig,
         is_save_csv=args.no_save_csv)

