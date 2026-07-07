"""Coordinate reference systems for the Delhi Metro digital twin.

The whole network sits within UTM zone 43N (EPSG:32643), which covers the Delhi
national-capital region including the far-flung extensions to Gurugram,
Ballabhgarh, Noida, Greater Noida and Ghaziabad. Storage is always WGS84
(EPSG:4326) decimal degrees; planar measurements (length, area, offsetting,
curvature via osculating circle) are done in UTM so the maths stays sane.
"""

from __future__ import annotations

from functools import lru_cache

import pyproj

# Canonical storage CRS — the one every geometry column is written in.
WGS84 = "EPSG:4326"

# Planar measurement CRS for the Delhi NCR. UTM zone 43N spans 75°E–81°E; all
# Delhi Metro lines lie well inside this band (Nangloi ~76.97°E, Noida ~77.50°E,
# Gurugram ~77.04°E, Ghaziabad/Shaheed Sthal ~77.46°E).
UTM43N = "EPSG:32643"

# Web Mercator — used only by the tile/GeoJSON emitters for map rendering.
WEB_MERCATOR = "EPSG:3857"


@lru_cache(maxsize=8)
def transformer(from_crs: str, to_crs: str, *, always_xy: bool = True) -> pyproj.Transformer:
    """Return a cached ``pyproj`` transformer between two CRSes.

    ``always_xy=True`` keeps the (x=lon, y=lat) convention everywhere, which is
    what every downstream consumer (Shapely, GeoJSON, PostGIS) expects.
    """
    return pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=always_xy)


def lonlat_to_utm(lon: float, lat: float) -> tuple[float, float]:
    """Project a WGS84 (lon, lat) to UTM 43N easting/northing in metres."""
    return transformer(WGS84, UTM43N).transform(lon, lat)


def utm_to_lonlat(easting: float, northing: float) -> tuple[float, float]:
    """Inverse of :func:`lonlat_to_utm`."""
    return transformer(UTM43N, WGS84).transform(easting, northing)
