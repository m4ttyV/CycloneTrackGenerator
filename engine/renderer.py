"""Matplotlib / Basemap renderer shared by CLI and future desktop front ends.

Call render_map() to get a matplotlib Figure, or render_png_bytes() to get
PNG data without a temporary file. Matplotlib pyplot is not thread-safe:
serialize render requests or run them in a dedicated worker process.
"""

from io import BytesIO
import os
import sys

import numpy as np
from mpl_toolkits.basemap import Basemap
from shapely.wkt import loads
import matplotlib.pyplot as plt

from .models import PreparedRows


def marker_type():
    """
            One day this function will return marker_type by type of cyclone or smth, but today its only "o"

    """
    return 'o'

def stage_type_id_color(type_id):
    """
            Returns marker edge color of stage by type id for tropical cyclones dots
            Args:
                type_id: type id of cyclone dots
            Returns:
               Color of stage by type id for tropical cyclones dots
    """
    if type_id == 2:
        return 'red'
    elif type_id == 6:
        return 'green'
    elif type_id == 7:
        return 'purple'
    elif type_id == 11:
        return 'orange'
    elif type_id == 29:
        return 'brown'

def track_tc(bm, tracks, DotRow):#1
    """
        Plots tropical cyc lone tracks on basemap.
        Args:
            bm: Basemap instance.
            tracks: Tropical cyclone dots tracks.
            DotRow: Row of dots.
    """
    for track in tracks:
        first_track_coord = True
        line = loads(track.coords)
        coords = list(line.coords)

        paired_coords = [(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
        for pair in paired_coords:
            first_coord, second_coord = pair
            first_coord_lon, first_coord_lat = first_coord
            for dot in DotRow:
                if dot.lon == first_coord_lon and dot.lat == first_coord_lat:
                    color = stage_type_id_color(dot.type_id)
                    lons, lats = zip(*list(pair))  # Разбираем координаты
                    x, y = bm(lons, lats)
                    bm.plot(x, y, marker=None, color=color, linewidth=2)
                    if first_track_coord:
                        plt.text(x[0] - 300000, y[0] - 300000, str(track.name).replace(' (', '\n('), fontsize=12, weight = "bold", color=color)
                        first_track_coord = False

def track_zn(bm, tracks):
    """
        Plots cyclone tracks on basemap.
        Args:
            bm: Basemap instance.
            tracks: Cyclone dots tracks.
    """
    for track in tracks:
        line = loads(track.coords)
        lons, lats = zip(*list(line.coords))  # Разбираем координаты
        x, y = bm(lons, lats)
        color = 'darkblue'
        bm.plot(x, y, marker=None, color=color, linewidth=2)
        plt.text(x[0] + 20000, y[0] + 20000, str(track.id).replace(' (', '\n('), fontsize=20, weight = "bold", color=color)

def track_az(bm, tracks):
    """
        Plots anticyclones tracks on basemap.
        Args:
            bm: Basemap instance.
            tracks: Anticyclones dots tracks.
    """
    for track in tracks:
        line = loads(track.coords)
        lons, lats = zip(*list(line.coords))  # Разбираем координаты
        x, y = bm(lons, lats)
        color = 'red'
        bm.plot(x, y, marker=None, color=color, linewidth=2)
        plt.text(x[0] + 20000, y[0] + 20000, str(track.id).replace(' (', '\n('), fontsize=20, weight = "bold", color=color)

def dot_tc(bm, dots):
    """
        Plots tropical cyclone dots on basemap.
        Args:
            bm: Basemap instance.
            dots: Tropical cyclone dots.
    """
    for dot in dots:
        color = stage_type_id_color(dot.type_id)
        x, y = bm(float(dot.lon), float(dot.lat))
        if dot.slp:
            plt.text(x + 20000, y + 20000, str(dot.slp), fontsize=12, color=color)
        datetime_str = str(dot.datetime)
        if datetime_str.split(' ')[1] == "00:00:00":
            datetime_row = dot.datetime.strftime('%d.%m')
            plt.text(x + 20000, y + 20000, datetime_row, fontsize=12, color=color)
        # будет функция возвращающая тип маркера (и цвет и тп)
        bm.plot(x, y, marker='o', color=color, markersize=5,  markeredgecolor=color, markerfacecolor='white')

def dot_zn(bm, dots):
    """
        Plots cyclone dots on basemap.
        Args:
            bm: Basemap instance.
            dots: Cyclone dots.
    """
    for dot in dots:
        color = 'blue'
        x, y = bm(float(dot.lon), float(dot.lat))
        marker = marker_type()
        bm.plot(x, y, marker=marker, color=color, markersize=5,  markeredgecolor=color, markerfacecolor='white')
        if dot.slp:
            plt.text(x + 20000, y + 20000, str(dot.slp), fontsize=12, color=color)

def dot_az(bm, dots):
    """
        Plots anticyclone dots on basemap.
        Args:
            bm: Basemap instance.
            dots: Anticyclone dots.
    """
    prev_dot_id = -1
    for dot in dots:
        color = 'red'
        x, y = bm(float(dot.lon), float(dot.lat))
        marker = marker_type()
        bm.plot(x, y, marker=marker, color=color, markersize=5,  markeredgecolor=color, markerfacecolor='white')
        if dot.slp:
            plt.text(x + 20000, y + 20000, str(dot.slp), fontsize=12, color=color)


def render_map(
    prepared: PreparedRows,
    cys_type_zn: bool,
    cys_type_az: bool,
    blanc_type: str,
):
    """Build a figure from already loaded and prepared data.

    The caller owns the returned figure and must close it with plt.close().
    This preserves the original projections, labels, legend and drawing order.
    """
    figure = None
    try:
        track_view_tc = prepared.track_view_tc
        track_view_zn = prepared.track_view_zn
        track_view_az = prepared.track_view_az
        mon_view_tc = prepared.mon_view_tc
        mon_view_zn = prepared.mon_view_zn
        mon_view_az = prepared.mon_view_az

        # Считываем карту и рисуем необходимую область
        os.environ['GDAL_DATA'] = os.path.join(f'{os.sep}'.join(sys.executable.split(os.sep)[:-1]), 'Library', 'share',
                                               'gdal')
        figure = plt.figure(figsize=(20, 16))

        if blanc_type == "TC":
            bm = Basemap(projection='aeqd',  # Тропики
                         lon_0=140,
                         lat_0=38,
                         width=9000000,
                         height=8000000,
                         resolution='i', area_thresh=1000.)
        else:
            bm = Basemap(projection='merc', llcrnrlat=20, urcrnrlat=65, \
                         llcrnrlon=105, urcrnrlon=190, lat_ts=20, resolution='i')

        bm.drawparallels(np.arange(-80., 81., 5.), labels=[True,False,True,False])
        bm.drawmeridians(np.arange(-180., 181., 5.), labels=[False,True,False,True])
        bm.drawcoastlines()


        # построение линий
        track_tc(bm, track_view_tc, mon_view_tc)
        track_zn(bm, track_view_zn)
        track_az(bm, track_view_az)

        # построение точек
        dot_tc(bm, mon_view_tc)
        dot_zn(bm, mon_view_zn)
        dot_az(bm, mon_view_az)


        # Легенда
        if blanc_type == "TC":
            x, y = bm(72, 57)
            bm.plot(x, y, marker='s', color="black", markersize=200, markeredgecolor="black",
                    markerfacecolor='white')
            x -= 700000

            cis_subtype_name = {
                2: "T",
                6: "TD",
                7: "STS",
                11: "TS",
                29: "L"
            }
            for color_id in [29, 6, 11, 7, 2]:
                bm.plot(x, y, marker='o', color="black", markersize=5, markeredgecolor=stage_type_id_color(color_id),
                        markerfacecolor='white')
                plt.text(x + 80000, y - 50000, cis_subtype_name[color_id], fontsize=12, weight="bold",
                         color="black")
                y -= 200000
        elif cys_type_zn and cys_type_az:
            x, y = bm(107, 62)
            x_s, y_s = bm(110, 63)
            both_line_X = (x, x + 200000)
            first_line_Y = (y, y)
            second_line_Y = (y + 150000, y + 150000)

            bm.plot(x_s, y_s, marker='s', color="black", markersize=200, markeredgecolor="black",
                    markerfacecolor='white')

            bm.plot(both_line_X, first_line_Y, marker=None, color="blue", linewidth=2)
            bm.plot(both_line_X, second_line_Y, marker=None, color="red", linewidth=2)
            bm.plot(x, y, marker='o', color="black", markersize=5, markeredgecolor="blue",
                    markerfacecolor='white')
            bm.plot(x + 200000, y, marker='o', color="black", markersize=5, markeredgecolor="blue",
                    markerfacecolor='white')
            bm.plot(x, y + 150000, marker='o', color="black", markersize=5, markeredgecolor="red",
                    markerfacecolor='white')
            bm.plot(x + 200000, y + 150000, marker='o', color="black", markersize=5, markeredgecolor="red",
                    markerfacecolor='white')
            plt.text(x + 300000, y - 30000, "Циклоны", fontsize=12, weight="bold", color="black")
            plt.text(x + 300000, y + 120000, "Антициклоны", fontsize=12, weight="bold", color="black")


        return figure
    except BaseException:
        if figure is not None:
            plt.close(figure)
        raise


def render_png_bytes(
    prepared: PreparedRows,
    cys_type_zn: bool,
    cys_type_az: bool,
    blanc_type: str,
    dpi: float | None = None,
) -> bytes:
    """Generate an in-memory PNG, independent of DB, CSV and SMB."""
    figure = render_map(prepared, cys_type_zn, cys_type_az, blanc_type)
    try:
        with BytesIO() as buffer:
            figure.savefig(
                buffer,
                format="png",
                bbox_inches="tight",
                pad_inches=0.1,
                dpi=dpi,
            )
            return buffer.getvalue()
    finally:
        plt.close(figure)
