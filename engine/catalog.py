"""Catalog of cyclone identities available for a generation period.

Uses only columns already referenced by the existing generator. Date filtering
intentionally matches its inclusive max_datetime selection.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


TYPE_NAMES = {1: "TC", 3: "ZN", 4: "AZ"}


@dataclass(frozen=True)
class CycloneInfo:
    cic_id: int
    cic_type_id: int
    name: Optional[str]
    first_observation: Optional[datetime]
    last_observation: Optional[datetime]
    observation_count: int

    @property
    def type_name(self) -> str:
        return TYPE_NAMES.get(self.cic_type_id, str(self.cic_type_id))


def list_cyclones(connection, date_start, date_end, cyclone_types=None) -> list[CycloneInfo]:
    """Return identities, optional names, and observation statistics.

    cyclone_types: None means all known categories; an empty sequence means none.
    Uses the same date filter as the existing map generator (max_datetime).
    """
    if cyclone_types is None:
        selected_types = tuple(TYPE_NAMES)
    else:
        selected_types = tuple(dict.fromkeys(cyclone_types))
        invalid = set(selected_types) - TYPE_NAMES.keys()
        if invalid:
            raise ValueError(f"Unsupported cyclone types: {sorted(invalid)}")
    if not selected_types:
        return []

    # Exclude large WKT tracks from this lightweight catalog query.
    with connection.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT ON (cic_id, cic_type_id) "
            "cic_id, cic_type_id, name "
            "FROM ciclones.cic_track_view_gs_full "
            "WHERE max_datetime >= %s AND max_datetime <= %s "
            "AND cic_type_id = ANY(%s) "
            "ORDER BY cic_id, cic_type_id, max_datetime DESC;",
            (date_start, date_end, list(selected_types)),
        )
        track_rows = cur.fetchall()

        cur.execute(
            "SELECT cic_id, cic_type_id, MIN(datetime), MAX(datetime), COUNT(*) "
            "FROM ciclones.cic_property_view_mon "
            "WHERE max_datetime >= %s AND max_datetime <= %s "
            "AND cic_type_id = ANY(%s) "
            "GROUP BY cic_id, cic_type_id;",
            (date_start, date_end, list(selected_types)),
        )
        point_rows = cur.fetchall()

    catalog = {}
    for cic_id, cic_type_id, name in track_rows:
        key = (cic_id, cic_type_id)
        catalog[key] = CycloneInfo(cic_id, cic_type_id, name, None, None, 0)

    for cic_id, cic_type_id, first, last, count in point_rows:
        key = (cic_id, cic_type_id)
        existing = catalog.get(key)
        catalog[key] = CycloneInfo(
            cic_id, cic_type_id,
            existing.name if existing else None,
            first, last, count,
        )

    return sorted(catalog.values(), key=lambda c: (c.cic_type_id, c.cic_id))
