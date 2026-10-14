"""
Generate the SAMPLE resource set and demo village geo (files only; no database is touched).

Everything here is SYNTHETIC. It exists so every label and state can be exercised (docs/DATA_PLAN.md
§4.1) and so the app can run with no real data. Each feature is placed by bearing and distance
from the demo plot, so the distances in the tests are exact.

    python scripts/make_sample_dataset.py
"""

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.livelihood.geo import destination  # noqa: E402

SEED = Path(__file__).resolve().parent.parent / "app" / "livelihood" / "seed"

# The demo plot, near the demo village (Ozhar, Jawhar, Palghar; approximate coordinates).
PLOT = (19.7805, 73.2210)
VILLAGE_CENTRE = (19.7800, 73.2200)
SOURCE = "VanMitra SAMPLE data (synthetic, not a real survey)"


def pt(bearing: float, dist_m: float) -> list[float]:
    lat, lng = destination(*PLOT, bearing, dist_m)
    return [round(lng, 6), round(lat, 6)]


def rect(
    centre_bearing: float, centre_dist_m: float, half_e: float, half_n: float
) -> dict[str, Any]:
    clat, clng = destination(*PLOT, centre_bearing, centre_dist_m)
    corners = []
    for de, dn in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)):
        lat, lng = destination(clat, clng, 90 if de > 0 else 270, half_e)
        lat, lng = destination(lat, lng, 0 if dn > 0 else 180, half_n)
        corners.append([round(lng, 6), round(lat, 6)])
    return {"type": "Polygon", "coordinates": [corners]}


def _river_line() -> list[list[float]]:
    """A north-south river 3 km west of the plot, 3 km long."""
    west = destination(*PLOT, 270, 3000)
    south = destination(*west, 180, 1500)
    north = destination(*west, 0, 1500)
    return [[round(p[1], 6), round(p[0], 6)] for p in (south, north)]


RIVER_LINE = _river_line()


def feature(rid: str, kind: str, geometry: dict[str, Any], **props: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": rid,
        "kind": kind,
        "district": "Palghar",
        "tag_hint": "none",
        "sensitive": False,
        "confidence": "low",
        "check_status": "to_verify",
        "attrs": {},
    }
    base.update(props)
    return {"type": "Feature", "geometry": geometry, "properties": base}


features = [
    feature(
        "smp_01_well",
        "well",
        {"type": "Point", "coordinates": pt(40, 420)},
        name_en="Sample well near the plot",
        name_mr="नमुना विहीर",
        attrs={"perennial": True, "months_available": 12, "condition": "good", "working": True},
    ),
    feature(
        "smp_02_checkdam",
        "water_structure",
        {"type": "Point", "coordinates": pt(120, 2000)},
        name_en="Sample check dam",
        name_mr="नमुना बंधारा",
        attrs={"perennial": False, "months_available": 4, "silted": True},
    ),
    feature(
        "smp_03_dry_pond",
        "water_body",
        {"type": "Point", "coordinates": pt(200, 1200)},
        name_en="Sample dry pond",
        name_mr="नमुना कोरडा तलाव",
        attrs={"dry": True, "perennial": False, "months_available": 2, "condition": "poor"},
    ),
    feature(
        "smp_04_river",
        "river",
        {"type": "LineString", "coordinates": RIVER_LINE},
        name_en="Sample river",
        name_mr="नमुना नदी",
        attrs={"perennial": True, "months_available": 12},
    ),
    feature(
        "smp_05_forest_cfr",
        "forest_compartment",
        rect(330, 1500, 300, 300),
        name_en="Sample community forest",
        name_mr="नमुना सामूहिक वन",
        tag_hint="cfr",
    ),
    feature(
        "smp_06_wildlife",
        "wildlife_compartment",
        rect(10, 2600, 300, 300),
        name_en="Sample wildlife compartment",
        name_mr="नमुना वन्यजीव विभाग",
    ),
    feature(
        "smp_07_tank_unchecked",
        "water_body",
        {"type": "Point", "coordinates": pt(80, 3500)},
        name_en="Sample tank (nothing checked)",
        name_mr="नमुना टाके (तपासलेले नाही)",
    ),
    feature(
        "smp_08_forest_large",
        "forest_compartment",
        rect(90, 6600, 2500, 1500),
        name_en="Sample large forest (centroid beyond 6 km, edge at 4.1 km)",
        name_mr="नमुना मोठे वन",
    ),
    feature(
        "smp_09_edge_inside",
        "water_body",
        {"type": "Point", "coordinates": pt(300, 4999)},
        name_en="Sample pond at 4,999 m",
        name_mr="नमुना तलाव ४९९९ मी",
        attrs={"perennial": False, "months_available": 6, "condition": "fair"},
    ),
    feature(
        "smp_10_edge_outside",
        "water_body",
        {"type": "Point", "coordinates": pt(250, 5001)},
        name_en="Sample pond at 5,001 m",
        name_mr="नमुना तलाव ५००१ मी",
        attrs={"perennial": True, "months_available": 12, "condition": "good"},
    ),
    feature(
        "smp_11_grazing",
        "grazing_land",
        rect(160, 2500, 400, 300),
        name_en="Sample grazing land (CFR approval)",
        name_mr="नमुना चराई जमीन",
        tag_hint="cfr",
        confidence="medium",
    ),
    feature(
        "smp_12_drainage",
        "drainage_line",
        {"type": "LineString", "coordinates": [pt(60, 900), pt(120, 1100)]},
        name_en="Sample drainage line",
        name_mr="नमुना ओढा",
        attrs={"perennial": False, "months_available": 5},
    ),
]

dataset = {
    "type": "FeatureCollection",
    "dataset": "sample_demo",
    "data_version": "v1",
    "is_sample": True,
    "source": SOURCE,
    "source_date": "2026-10-14",
    "features": features,
}
(SEED / "sample_resources.geojson").write_text(
    json.dumps(dataset, ensure_ascii=False, indent=1), encoding="utf-8"
)

cfr = rect(
    330, 1500, 700, 700
)  # a SAMPLE community-forest shape around the sample forest, not real
village = {
    "village_id": "sample_ozhar",
    "name_mr": "ओझर",
    "name_en": "Ozhar",
    "centroid_lat": VILLAGE_CENTRE[0],
    "centroid_lng": VILLAGE_CENTRE[1],
    "boundary": None,
    "cfr_polygons": [cfr],
    "source": "SAMPLE: approximate village centre; sample CFR shape, not the real boundary",
    "source_date": "2026-10-14",
    "is_sample": True,
}
(SEED / "sample_village_geo.json").write_text(
    json.dumps(village, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(f"wrote {len(features)} sample features and the demo village to {SEED}")
