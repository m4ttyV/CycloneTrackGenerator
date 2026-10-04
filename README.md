# CycloneTrackGenerator — генератор карт и CSV треков циклонов (ZN/AZ/TC)

Скрипт строит карты треков **циклонов**, **антициклонов** и **тропических циклонов**, выгружает точки в CSV и (опционально) загружает результаты на SMB-шару. Данные выбираются из PostgreSQL по готовым представлениям, визуализация делается на **Basemap**, экспорт в PNG/CSV — локально и/или на SMB. ;

---

## Возможности

* Запрос треков и точек за заданный период из БД (PostgreSQL)
  (`ciclones.cic_track_view_gs_full`, `ciclones.cic_property_view_mon`).;
* Построение карты:

  * **ZN** — циклоны (синие линии/точки),
  * **AZ** — антициклоны (красные линии/точки),
  * **TC** — тропические циклоны с цветами стадий (T/TD/TS/STS/L).;
* Подписи давлений точек (опционально, в моменты 00:00 UTC) и имён треков.;
* Экспорт PNG-карт и CSV по типам (ZN/AZ/TC) c фиксированным форматом колонок.;
* Автосоздание директорий на SMB и загрузка итоговых файлов.;

---

## Зависимости

Python 3.9+

```bash
pip install psycopg2-binary shapely numpy matplotlib basemap-python python-dateutil smbprotocol smbclient
```

> Примечания:
>
> * **Basemap** требует установленные **GEOS/PROJ**; на Windows чаще ставят колесо `basemap-python`.
> * Для `smbclient`/`smbprotocol` может потребоваться Microsoft C++ Build Tools/libs.

---

## Конфигурация (файл `confing.conf`)

Скрипт читает конфиг **построчно** (строго в этом порядке):
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SMB_HOST`, `SMB_USERNAME`, `SMB_PASSWORD`, `SMB_SHARE`.
Файл должен лежать рядом со скриптом.;

Пример `confing.conf`:

```
db.example.local
5432
ciclones
report_user
s3cr3t
fileserver.local
DOMAIN\report_user
p@ssw0rd
METEO
```

---

## Как запустить

### 1) Из консоли

```bash
python main.py \
  --startdate 2025-01-01 \
  --period 0 \
  --cyclone 1 \
  --anticyclone 1 \
  --tropicalcyclone 0 \
  --pathtosave "D:/tmp/results/" \
  --dots_slp 1 \
  --track_name 1 \
  --blanc_type None
```

Аргументы CLI:;

| Параметр                 |   Тип | По умолчанию       | Описание                                           |
| ------------------------ | ----: | ------------------ | -------------------------------------------------- |
| `--startdate, -sd`       |   str | `2025-01-01`       | Дата начала периода `YYYY-MM-DD`                   |
| `--period, -p`           |   int | `0`                | Тип периода: `0` — месяц, `1` — декада             |
| `--cyclone, -zn`         |   int | `1`                | Строить циклоны (ZN): `1/0`                        |
| `--anticyclone, -az`     |   int | `1`                | Строить антициклоны (AZ): `1/0`                    |
| `--tropicalcyclone, -tc` |   int | `0`                | Строить тропические циклоны (TC): `1/0`            |
| `--pathtosave, -pts`     |   str | `D:/tmp/test2506/` | Путь для сохранения (префикс имени)                |
| `--dots_slp, -slp`       | float | `0`                | Подписи давления точек (только в 00:00 UTC): `1/0` |
| `--track_name, -tn`      |   int | `1`                | Подписывать имена линий: `1/0`                     |
| `--blanc_type, -bt`      |   str | `None`             | Макет карты: `None` (ZN/AZ) или `TC`               |

> В коде есть примеры «массового» запуска по месяцу/декадам (закомментированы в `main.py`).;

### 2) Что делает программа внутри

* Формирует период: для `period=0` — календарный месяц; для `period=1` — декада от `startdate`.;
* Запрашивает из БД:

  * треки (`ST_AsText(track)`… `ciclones.cic_track_view_gs_full`),
  * точки (`ST_X(coord)`, `ST_Y(coord)`… `ciclones.cic_property_view_mon`).;
* Рисует карту:

  * **ZN/AZ** — проекция Mercator на (105–190E, 20–65N),
  * **TC** — проекция Azimuthal Equidistant, `lon_0=140`, `lat_0=45`.;
* Цвета TC по `type_id`: 2=T (красный), 6=TD (зелёный), 7=TS (оранжевый), 11=STS (фиолет), 29=L (коричневый). Легенда добавляется автоматически.;
* Подписи давлений точек — если `--dots_slp=1`, в записи с часом `00:00`. Подписи имён треков — при `--track_name=1`.;
* Сохраняет файлы и, если настроен SMB, заливает их на шару.;

---

## Выходные файлы

### PNG-карта

Имя собирается как:

```
{pathtosave}{YYYYMMDD}_{month|decade}_{types}.png
# пример: D:/tmp/results/20250101_month_ZN_AZ.png
```

Где `types` — комбинация `ZN`/`AZ`/`TC` согласно выбранным опциям.;

### CSV по типам

Создаются по тем же префиксам: `...ZN.csv`, `...AZ.csv`, `...TC.csv`.
Формат (разделитель `;`, `utf-8-sig`): заголовок `id;datetime;lat;lon;slp`, строки — целочисленные `lat/lon/slp`, `datetime` в формате `YYYY.MM.DD`.;

---

## SMB-загрузка (необязательно)

Если заданы параметры SMB в `confing.conf`, итоговые файлы будут загружены в каталог:

```
\\{SMB_HOST}\{SMB_SHARE}\bulletin/{YYYY.MM}/DATA/1 МЕТЕО/Циклоны/{d}/
```

Где `{d}` автоматически определяется по наличию `d1`/`d2`/`d3` в локальном пути файла. Каталоги создаются при необходимости.;

---

## Архитектура кода

* `main.py` — парсинг аргументов CLI и запуск `main(...)`.;
* `functions.py` — основная логика:

  * классы `TrackRow`, `DotRow`, `CSVRow`;
  * запросы к БД (`get_cis_property_view_month`, `get_cis_track_view_month`);
  * отрисовка линий/точек (`track_*`, `dot_*`);
  * экспорт CSV (`csv_gen`);
  * SMB-утилиты (`ensure_remote_directory`, `upload_file_to_smb`);
  * `main(...)` — сборка всего пайплайна.;

---

## Переменные окружения

Для корректной работы Basemap в некоторых средах задаётся GDAL:
устанавливается автоматически в коде из каталога Python:
`os.environ['GDAL_DATA'] = <...>/Library/share/gdal`.;

---

## Частые проблемы

* **SMB: STATUS\_LOGON\_FAILURE (0xc000006d)** — проверьте файл конфигурации: нет ли скрытых символов/BOM, формат логина `DOMAIN\user`, корректность пароля и прав доступа на шару. (В проекте значения читаются «как есть» построчно).;
* **Basemap/GEOS/PROJ** — убедитесь, что библиотеки поставлены (особенно на Windows).
* **PostgreSQL доступ** — нужные представления/поля должны существовать и соответствовать запросам.;

---

## Примеры сценариев

* **Месяц, ZN+AZ, без TC**:

  ```bash
  python main.py -sd 2025-03-01 -p 0 -zn 1 -az 1 -tc 0 -pts D:/maps/mar/ -slp 1 -tn 1 -bt None
  ```
* **Декада, только TC-бланк:**

  ```bash
  python main.py -sd 2025-07-01 -p 1 -zn 0 -az 0 -tc 1 -pts D:/maps/jul/ -slp 0 -tn 1 -bt TC
  ```

---

