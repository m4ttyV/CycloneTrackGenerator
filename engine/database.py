"""Read-only queries used to load cyclone tracks and observation points."""


def get_cis_property_view_month(date_start, date_end, cur):
    """Retrieve observation points with the historical ordering and boundaries."""
    cur.execute(
        "SELECT ST_X(coord), ST_Y(coord), cic_type_id, * "
        "FROM ciclones.cic_property_view_mon "
        "WHERE max_datetime >= %s AND max_datetime <= %s "
        "ORDER BY cic_id, datetime;",
        (date_start, date_end),
    )
    return cur.fetchall()


def get_cis_track_view_month(date_start, date_end, cur):
    """Retrieve trajectories with the historical ordering and boundaries."""
    cur.execute(
        "SELECT ST_AsText(track), cic_type_id, * "
        "FROM ciclones.cic_track_view_gs_full "
        "WHERE max_datetime >= %s AND max_datetime <= %s "
        "ORDER BY cic_id, max_datetime;",
        (date_start, date_end),
    )
    return cur.fetchall()


def load_source_rows(connection, date_start, date_end):
    """Fetch rows and close the cursor even if a query raises an error.

    The caller owns the database connection and must close it.
    """
    with connection.cursor() as cur:
        points = get_cis_property_view_month(date_start, date_end, cur)
        tracks = get_cis_track_view_month(date_start, date_end, cur)
    return points, tracks
