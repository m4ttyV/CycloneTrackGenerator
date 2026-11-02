"""Render-ready records extracted from the database's legacy positional rows."""

from dataclasses import dataclass, field


@dataclass
class TrackRow:
    coords: str
    name: str
    id: str


@dataclass
class DotRow:
    lon: float
    lat: float
    type_id: int | None
    slp: object
    datetime: object


@dataclass
class CSVRow:
    id: str
    datetime: object
    lon: float
    lat: float
    slp: object


@dataclass
class PreparedRows:
    track_view_tc: list[TrackRow] = field(default_factory=list)
    track_view_zn: list[TrackRow] = field(default_factory=list)
    track_view_az: list[TrackRow] = field(default_factory=list)
    mon_view_tc: list[DotRow] = field(default_factory=list)
    mon_view_zn: list[DotRow] = field(default_factory=list)
    mon_view_az: list[DotRow] = field(default_factory=list)
    csv_dot_tc: list[CSVRow] = field(default_factory=list)
    csv_dot_zn: list[CSVRow] = field(default_factory=list)
    csv_dot_az: list[CSVRow] = field(default_factory=list)


def prepare_rows(
    track_view_rows,
    view_mon_rows,
    cys_type_zn: bool,
    cys_type_az: bool,
    cys_type_tc: bool,
    is_slp: bool,
    is_track_name: bool,
) -> PreparedRows:
    """Preserve the legacy type filtering, positional indexes and labels.

    This is intentionally independent of PostgreSQL and Matplotlib, allowing
    callers to reuse fetched rows without rerunning SQL.
    """
    prepared = PreparedRows()
    enabled = {
        1: (cys_type_tc, prepared.track_view_tc),
        3: (cys_type_zn, prepared.track_view_zn),
        4: (cys_type_az, prepared.track_view_az),
    }

    for track in track_view_rows:
        track_type = track[1]
        row = track[0]
        setting = enabled.get(track_type)
        if setting is None or not setting[0] or row is None:
            continue
        track_id = str(track[2])[-2:] if is_track_name else ""
        name = (track[3] if track[3] is not None else "") if is_track_name else ""
        setting[1].append(TrackRow(row, name, track_id))

    point_groups = {
        1: (cys_type_tc, prepared.mon_view_tc, prepared.csv_dot_tc),
        3: (cys_type_zn, prepared.mon_view_zn, prepared.csv_dot_zn),
        4: (cys_type_az, prepared.mon_view_az, prepared.csv_dot_az),
    }
    for dot in view_mon_rows:
        dot_type = dot[2]
        setting = point_groups.get(dot_type)
        if setting is None or not setting[0]:
            continue

        datetime_dot = dot[15]
        # Pressure labels in the original generator appear only at 00 UTC.
        pressure_label = dot[18] if datetime_dot.strftime("%H") == "00" and is_slp else ""
        subtype = dot[13] if dot[13] else None
        setting[1].append(DotRow(dot[0], dot[1], subtype, pressure_label, datetime_dot))
        setting[2].append(
            CSVRow(str(dot[4])[-2:], datetime_dot, dot[0], dot[1], dot[18])
        )
    return prepared
