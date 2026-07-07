# dmdt-gis

The GIS layer of the Delhi Metro Digital Twin. It owns the canonical geographic
representation of the operational network: lines, stations, platforms, track
segments, crossovers, depots, sidings, junctions and switches.

## What lives here

| Path | Purpose |
|---|---|
| `dmdt_gis/geometry.py` | Geodesic + planar geometry helpers (distance, bearing, curvature, offsetting, polygon synthesis). Pure functions, no I/O. |
| `dmdt_gis/dataset.py` | Programmatic access to the canonical network dataset (`gis/data/network.json`). |
| `dmdt_gis/geojson.py` | Emit GeoJSON FeatureCollections for lines, stations, track segments, depots, platforms. |
| `dmdt_gis/track.py` | Build `LineString` track geometries from ordered station waypoints, with curvature/speed-limit metadata per segment. |
| `dmdt_gis/crs.py` | Coordinate reference-system constants and transformers (EPSG:4326 ↔ EPSG:32643 UTM 43N, the Delhi UTM zone). |
| `dmdt_gis/wkb.py` | WKB/WKT <-> Shapely geometry conversion used by the seed loader. |
| `gis/data/network.json` | The canonical Delhi Metro network dataset (lines, stations, depots, track geometry, speed limits). Authored from public DMRC data; each station carries a `coordinate_confidence` field. |
| `gis/layers/` | Generated GeoJSON layers (lines.geojson, stations.geojson, …) |
| `gis/tools/` | CLI tooling (`build_layers.py`) that regenerates the GeoJSON layers from `network.json`. |

## Coordinate system

All stored coordinates are WGS84 (EPSG:4326), decimal degrees. Planar
computations (length, area, offsetting) are performed in EPSG:32643 (UTM zone
43N), which spans the Delhi national-capital region. Distances returned to
callers are in metres; speeds in km/h.

## Usage

```python
from dmdt_gis.dataset import load_network
net = load_network()
red = net.line("RD")
for seg in red.track_segments:
    print(seg.from_station, "->", seg.to_station, f"{seg.length_m:.0f} m")
```

## Tests

```bash
pip install -e .[dev]
pytest -q
```
