"""Read-only record cards. IDs come from the rendered objects."""
from datetime import date, datetime
import math


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def get_record(connection, kind, key):
    if kind == "observation":
        query = """
            SELECT cp.id, cp.cic_id, cp.datetime, ST_X(cp.coord::geometry) AS lon,
                   ST_Y(cp.coord::geometry) AS lat, cp.slp, cp.velocity, cp.wind_max,
                   cp.wind_radius_50_1, cp.wind_radius_50_2,
                   cp.wind_radius_30_1, cp.wind_radius_30_2, cp.direction_rumb,
                   cp.cic_stage_type_id, ct.name_rus AS stage_name, cp.info, cp.dti
            FROM ciclones.cic_property cp
            LEFT JOIN ciclones.cic_type ct ON ct.id = cp.cic_stage_type_id
            WHERE cp.id = %s
        """
    elif kind == "cyclone":
        query = """
            SELECT c.id, c.name, c.cic_type_id, ct.name_rus AS type_name,
                   c.cic_sub_type_id, st.name_rus AS subtype_name,
                   c.datasource_id, ds.name_rus AS datasource_name, c.info, c.dti, c.dtu
            FROM ciclones.cic c
            LEFT JOIN ciclones.cic_type ct ON ct.id = c.cic_type_id
            LEFT JOIN ciclones.cic_type st ON st.id = c.cic_sub_type_id
            LEFT JOIN ciclones.cic_type ds ON ds.id = c.datasource_id
            WHERE c.id = %s
        """
    else:
        raise ValueError("Unsupported record kind")
    with connection.cursor() as cursor:
        cursor.execute(query, (key,))
        row = cursor.fetchone()
        if row is None:
            raise LookupError("Record no longer exists; rebuild the preview")
        return {column[0]: _json_value(value) for column, value in zip(cursor.description, row)}


def get_dictionaries(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name_rus, dic_part FROM ciclones.cic_type
            WHERE dic_part IN ('Тип', 'Подтип', 'Стадия', 'Источник') AND id <> 16
            ORDER BY dic_part, id
        """)
        return [{"id": row[0], "name": row[1], "category": row[2]}
                for row in cursor.fetchall()]
