from functions import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate cyclone, anticyclone and tropical cyclone track maps from PostgreSQL data.")
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
    # Эта шляпа нужна для прогонки по конкретному месяцу(ем)
    # Циклоны и антициклоны
    # for month in [8]:
    #     for dec in [0,1,2]:
    #         dt = datetime(2025, month=month, day=dec * 10 + 1)
    #
    #         print(dt)
    #         main(True, True, False, dt.strftime('%Y-%m-%d'), 1, f'D:/tmp/test1508/results/{month:02d}/{dec + 1}/ZN_AZ_m{month:02d}_d{dec + 1}', False, True, "None")
    #         main(False, True, False, dt.strftime('%Y-%m-%d'), 1, f'D:/tmp/test1508/results/{month:02d}/{dec + 1}/AZ_m{month:02d}_d{dec + 1}', False, True, "None")
    #         main(True, False, False, dt.strftime('%Y-%m-%d'), 1, f'D:/tmp/test1508/results/{month:02d}/{dec + 1}/ZN_m{month:02d}_d{dec + 1}', False, True, "None")
    #
    #     dt = datetime(2025, month=month, day=1)
    #     print(dt)
    #     main(True, True, False, dt.strftime('%Y-%m-%d'), 0, f'D:/tmp/test1508/results/{month:02d}/ZN_AZ_m{month:02d}_', False, True, "None")
    #     main(False, True, False, dt.strftime('%Y-%m-%d'), 0, f'D:/tmp/test1508/results/{month:02d}/AZ_m{month:02d}_', False, True, "None")
    #     main(True, False, False, dt.strftime('%Y-%m-%d'), 0, f'D:/tmp/test1508/results/{month:02d}/ZN_m{month:02d}_', False, True, "None")
    #     # Тропики
    #     main(False, False, True, dt.strftime('%Y-%m-%d'), 0, f'D:/tmp/test1508/results/{month:02d}/TC_m{month:02d}_', False, True, "TC")

    main(cis_type_zn, cis_type_az, cis_type_tc, args.startdate, args.period, args.pathtosave, is_slp, is_track_name, blanc_type)

