import csv
import smbclient
import psycopg2
import os
from datetime import datetime
import matplotlib.pyplot as plt
from engine.config import load_config
from engine.database import load_source_rows, get_cis_property_view_month, get_cis_track_view_month
from engine.periods import calculate_period
from engine.models import TrackRow, DotRow, CSVRow, prepare_rows
from engine.renderer import render_map, render_png_bytes, marker_type, stage_type_id_color, track_tc, track_zn, track_az, dot_tc, dot_zn, dot_az

def ensure_remote_directory(host: str, share: str, path: str):
    """
            Check if remote directory exists and create it if not.

            Args:
                host: (str) host of SMB-dir.
                share: (str) share of SMB-dir
                path: (str) path to check in SMB-dir.
    """
    parts = path.strip("/").split("/")
    unc = rf"\\{host}\{share}"
    for part in parts:
        unc = rf"{unc}\{part}"
        try:
            smbclient.listdir(unc)
        except Exception:
            smbclient.mkdir(unc)
            print(f"Создана директория: {unc}")

def upload_file_to_smb(SMB_HOST, SMB_USERNAME, SMB_PASSWORD, SMB_SHARE, local_file_path, file_date):
    """
        Upload local files to SMB
        Args:
            SMB_HOST: (str) host of SMB-server.
            SMB_USERNAME: (str) username of SMB-server.
            SMB_PASSWORD: (str) password of SMB-server.
            SMB_SHARE: (str) share of SMB-server.
            local_file_path: (str) path to local file to upload.
            file_date: (str) date of file to upload.

        Returns:
           float Depth calculated from the input netCDF.

    """
    local_file_path = local_file_path.replace('\\', '/')
    file_name = os.path.basename(local_file_path)
    dec = ""
    if ("d1" in local_file_path):
        dec = "1/"
    if ("d2" in local_file_path):
        dec = "2/"
    if ("d3" in local_file_path):
        dec = "3/"

    smb_path = f"bulletin/{file_date}/DATA/1 МЕТЕО/Циклоны/" + dec


    smbclient.register_session(
    server=SMB_HOST,
    username=SMB_USERNAME,
    password=SMB_PASSWORD)
    tmp = "bulletin"
    test_dir = rf"\\{SMB_HOST}\{SMB_SHARE}\{tmp}"
    remote_dir = rf"\\{SMB_HOST}\{SMB_SHARE}\{smb_path}"
    remote_file = rf"{remote_dir}\{file_name}"
    try:
        files = smbclient.listdir(test_dir)
        print("Соединение установлено, в папке найдено файлов:", len(files))
    except Exception as e:
        print("Не удалось подключиться к SMB-шаре:", e)
    ensure_remote_directory(SMB_HOST, SMB_SHARE, smb_path)
    try:
        with open(local_file_path, "rb") as src, \
            smbclient.open_file(remote_file, mode="wb") as dst:
            dst.write(src.read())
        print(f"Файл {file_name} успешно загружен в {smb_path}")
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
    print()
    # pass

def csv_gen(filename, csv_row): #id, datetime, lat, lon, slp
    """
        Function for generating CSV-file
        Args:
            filename: filepath for CSV file.
            csv_row: class object for generating CSV file.

    """
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["id", "datetime", "lat", "lon", "slp"])
        for row in csv_row:
            writer.writerow([
                str(row.id),
                str(row.datetime.strftime("%Y.%m.%d")),
                str(int(row.lat)), #широта
                str(int(row.lon)), #долгота
                str(int(row.slp))  #давление
            ])


def main(cys_type_zn, cys_type_az, cys_type_tc, start_date, period, save_path, is_slp,
         is_track_name, blanc_type, is_smb, is_save_fig, is_save_csv=True, selected_cic_ids=None):  # Циклон, Антициклон, Тропический циклон
    """
        Main function.
        Args:
            cys_type_zn: cyclone movement points.
            cys_type_az: anticyclone movement points.
            cys_type_tc: tropical cyclone movement tracks.
            start_date: start date of cyclone movement points.
            period: period of cyclone movement points.
            save_path: path to save CSV file.
            is_slp: type "True" if you need to plot pressure of cyclone movement points basemap or "False" otherwise.
            is_track_name: type "True" if you need to plot names of tracks on basemap or "False" otherwise.
            blanc_type: "None" for cyclones or anticyclones and "TC" for tropical cyclones.
            is_save_csv: whether CSV datasets should be written (defaults to True for CLI compatibility).\n            selected_cic_ids: optional full IDs; None preserves unfiltered generation.
    """
    save_dir = save_path.rsplit('/', 1)[0]
    try:
        os.makedirs(save_dir)
    except:
        pass

    # Historical config filename and lookup are preserved.
    config = load_config("confing.conf")
    start_date, end_date = calculate_period(start_date, period)

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    try:
        if selected_cic_ids is None:\n            view_mon_rows, track_view_rows = load_source_rows(conn, start_date, end_date)\n        else:\n            view_mon_rows, track_view_rows = load_source_rows(\n                conn, start_date, end_date, selected_cic_ids=selected_cic_ids\n            )
    finally:
        conn.close()

    prepared = prepare_rows(
        track_view_rows, view_mon_rows,
        cys_type_zn, cys_type_az, cys_type_tc,
        is_slp, is_track_name,
    )
    # формирование имени файла и пути
    file_date = str(datetime.strftime(start_date, "%Y%m%d"))
    filepath = save_path + file_date
    if period == 0:
        filepath = filepath + "_month_"
    elif period == -1:
        filepath = filepath + "_decade_"
    else:
        filepath = filepath + "_custom_"
    csv_filepath = filepath
    if cys_type_zn:
        filepath = filepath + "ZN"
    if cys_type_az:
        filepath = filepath + "AZ"
    if cys_type_tc:
        filepath = filepath + "TC"
    filepath += ".png"

    # Rendering is independent from PostgreSQL and CSV / SMB export.
    figure = render_map(prepared, cys_type_zn, cys_type_az, blanc_type)
    try:
        if is_save_fig:
            figure.savefig(filepath, bbox_inches="tight", pad_inches=0.1)
    finally:
        plt.close(figure)

    if is_smb and is_save_fig: upload_file_to_smb(config.smb_host, config.smb_username, config.smb_password, config.smb_share,
        filepath, str(datetime.strftime(start_date, "%Y.%m")))

    # написание csv файлов
    if is_save_csv and cys_type_az:
        csv_gen(f"{csv_filepath}AZ.csv", prepared.csv_dot_az)
        if is_smb and is_save_fig: upload_file_to_smb(config.smb_host, config.smb_username, config.smb_password, config.smb_share,
                           f"{csv_filepath}AZ.csv", str(datetime.strftime(start_date, "%Y.%m")))
    if is_save_csv and cys_type_zn:
        csv_gen(f"{csv_filepath}ZN.csv", prepared.csv_dot_zn)
        if is_smb and is_save_fig: upload_file_to_smb(config.smb_host, config.smb_username, config.smb_password, config.smb_share,
                           f"{csv_filepath}ZN.csv", str(datetime.strftime(start_date, "%Y.%m")))
    if is_save_csv and cys_type_tc:
        csv_gen(f"{csv_filepath}TC.csv", prepared.csv_dot_tc)
        if is_smb and is_save_fig: upload_file_to_smb(config.smb_host, config.smb_username, config.smb_password, config.smb_share,
                           f"{csv_filepath}TC.csv", str(datetime.strftime(start_date, "%Y.%m")))

# 1 - тропический циклон TC
# 2 -
# 3 - циклон ZN
# 4 - антициклон AZ
