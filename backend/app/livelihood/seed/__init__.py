"""Loaders for the bundled seed files (idea library, SAMPLE resources, demo village, weather)."""

import json
from pathlib import Path
from typing import Any

from ..schemas import Idea, ResourceRecord, VillageGeo, WeatherMonth, WeatherOut

_DIR = Path(__file__).parent


def _read(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((_DIR / name).read_text(encoding="utf-8"))
    return data


def load_ideas() -> list[Idea]:
    return [Idea.model_validate(i) for i in _read("ideas.json")["ideas"]]


def load_sample_dataset() -> tuple[dict[str, Any], list[ResourceRecord]]:
    """The SAMPLE resource set: returns (dataset header, records). Every record is is_sample."""
    raw = _read("sample_resources.geojson")
    header = {k: v for k, v in raw.items() if k != "features"}
    records: list[ResourceRecord] = []
    for feature in raw["features"]:
        props = dict(feature["properties"])
        records.append(
            ResourceRecord(
                id=props.pop("id"),
                geometry=feature["geometry"],
                dataset=header["dataset"],
                is_sample=bool(header["is_sample"]),
                source=header["source"],
                source_date=header["source_date"],
                **props,
            )
        )
    return header, records


def load_demo_village() -> VillageGeo:
    return VillageGeo.model_validate(_read("sample_village_geo.json"))


def load_sample_weather() -> WeatherOut:
    raw = _read("sample_weather.json")
    return WeatherOut(
        is_sample=True,
        months=[WeatherMonth.model_validate(m) for m in raw["months"]],
    )
