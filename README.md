# CycloneTrackGenerator

Python CLI tool for generating cyclone, anticyclone and tropical cyclone track maps from PostgreSQL data.

The application retrieves atmospheric system tracks and observation points from PostgreSQL, visualizes them on geographic maps, exports CSV datasets and can optionally upload generated results to an SMB share.

## Features

- PostgreSQL-based cyclone track retrieval
- Cyclone (ZN), anticyclone (AZ) and tropical cyclone (TC) support
- Monthly and ten-day period processing
- Geographic track visualization
- Tropical cyclone stage visualization
- Optional pressure labels
- Optional track-name labels
- PNG map export
- CSV track export
- Optional SMB upload
- Command-line interface for batch processing

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| PostgreSQL | Cyclone and track data source |
| Psycopg2 | PostgreSQL access |
| Matplotlib | Plot rendering |
| Basemap | Geographic visualization |
| Shapely | Geometry processing |
| SMBProtocol | SMB file transfer |

## Processing Pipeline

```text
PostgreSQL
    │
    ▼
Track and point queries
    │
    ▼
Cyclone classification
ZN / AZ / TC
    │
    ▼
Geographic visualization
    │
    ├── PNG maps
    └── CSV datasets
             │
             ▼
      Optional SMB upload
```
