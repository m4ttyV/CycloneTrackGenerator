"""Read-only queries used to load cyclone tracks and observation points."""


def get_cis_property_view_month(date_start, date_end, cur, selected_cic_ids=None):
    """Retrieve observation points with the historical ordering and boundaries."""
    if selected_cic_ids is not None and not selected_cic_ids:
        return []
    query = (
        "SELECT ST_X(coord), ST_Y(coord), cic_type_id, * "
        "FROM ciclones.cic_property_view_mon "
        "WHERE max_datetime >= %s AND max_datetime <= %s "
    )
    params = [date_start, date_end]
    if selected_cic_ids is not None:
        query += "AND cic_id = ANY(%s) "
        params.append(list(selected_cic_ids))
    query += "ORDER BY cic_id, datetime;"
    cur.execute(query, tuple(params))
    return cur.fetchall()


def get_cis_track_view_month(date_start, date_end, cur, selected_cic_ids=None):
    """Retrieve trajectories with the historical ordering and boundaries."""
    if selected_cic_ids is not None and not selected_cic_ids:
        return []
    query = (
        "SELECT ST_AsText(track), cic_type_id, * "
        "FROM ciclones.cic_track_view_gs_full "
        "WHERE max_datetime >= %s AND max_datetime <= %s "
    )
    params = [date_start, date_end]
    if selected_cic_ids is not None:
        query += "AND cic_id = ANY(%s) "
        params.append(list(selected_cic_ids))
    query += "ORDER BY cic_id, max_datetime;"
    cur.execute(query, tuple(params))
    return cur.fetchall()


def load_source_rows(connection, date_start, date_end, selected_cic_ids=None):
    """Fetch rows and close the cursor even if a query raises an error.\n\n    selected_cic_ids=None retains the old unfiltered behavior. An empty\n    selection fetches nothing. Filtering applies to tracks and points.

    The caller owns the database connection and must close it.
    """
    if selected_cic_ids is not None:
        selected_cic_ids = tuple(dict.fromkeys(selected_cic_ids))
        if not selected_cic_ids:
            return [], []
    with connection.cursor() as cur:
        points = get_cis_property_view_month(date_start, date_end, cur, selected_cic_ids)
        tracks = get_cis_track_view_month(date_start, date_end, cur, selected_cic_ids)
    return points, tracks
