"""
Livelihood routes, mounted at /api/v1/livelihood.

Slice 1 (this file): the stateless DEMO routes. They build a report from the bundled SAMPLE
dataset, store nothing, and need no login, so the app can run end to end before the database
and auth slice exists. They are switched by VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS and must be OFF
anywhere real data or real users are involved.

Slice 2 adds the real routes (docs/BACKEND_PLAN.md §3): PUT/GET/DELETE /profile, POST /report,
GET /report/latest, POST /resources/nearby, all scoped to the signed-in user.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import get_settings
from ..errors import ApiError
from .domain.config import DEFAULT_CONFIG
from .domain.units import AreaUnit
from .schemas import ANIMAL_CODES, ASSET_CODES, PAST_WORK_CODES, ProfileIn, ReportOut
from .seed import (
    load_demo_village,
    load_ideas,
    load_sample_dataset,
    load_sample_weather,
)
from .service import DatasetMeta, build_report

router = APIRouter(prefix="/livelihood", tags=["livelihood"])

DEMO_PLOT = {
    "lat": 19.7805,
    "lng": 73.2210,
}  # inside the sample dataset's 5 km (see seed generator)


class DemoReportRequest(BaseModel):
    profile: ProfileIn | None = None
    radius_m: int | None = None
    name: str = "Demo villager"


def _require_demo() -> None:
    if not get_settings().livelihood_demo_endpoints:
        raise ApiError(404, "NOT_FOUND", "error.not_found")


@router.get("/meta")
def meta() -> dict[str, Any]:
    """What the form needs: vocabularies, radius limits, and which dataset is loaded."""
    header, _ = load_sample_dataset()
    settings = get_settings()
    return {
        "default_radius_m": settings.livelihood_default_radius_m,
        "max_radius_m": settings.livelihood_max_radius_m,
        "area_units": [u.value for u in AreaUnit],
        "asset_codes": list(ASSET_CODES),
        "animal_codes": list(ANIMAL_CODES),
        "past_work_codes": list(PAST_WORK_CODES),
        "dataset": {
            "name": header["dataset"],
            "data_version": header["data_version"],
            "is_sample": header["is_sample"],
            "source": header["source"],
        },
        "demo_plot": DEMO_PLOT,
        "bands": {  # labels only; the numbers behind them are never sent to the app (rule L5)
            "resource": ["useful", "partly_useful", "not_useful"],
            "fit": ["good", "fair", "weak"],
        },
    }


@router.post("/demo/report", response_model=ReportOut)
def demo_report(body: DemoReportRequest) -> ReportOut:
    """A full report from the SAMPLE dataset for the details given. Stores nothing."""
    _require_demo()
    header, records = load_sample_dataset()
    settings = get_settings()
    cfg = DEFAULT_CONFIG
    if (
        settings.livelihood_default_radius_m != cfg.default_radius_m
        or settings.livelihood_max_radius_m != cfg.max_radius_m
    ):
        from dataclasses import replace

        cfg = replace(
            cfg,
            default_radius_m=settings.livelihood_default_radius_m,
            max_radius_m=settings.livelihood_max_radius_m,
        )
    return build_report(
        profile=body.profile,
        user_name=body.name,
        village=load_demo_village(),
        resources=records,
        ideas=load_ideas(),
        dataset=DatasetMeta(
            name=header["dataset"],
            data_version=header["data_version"],
            is_sample=header["is_sample"],
            source=header["source"],
            source_date=header["source_date"],
        ),
        cfg=cfg,
        radius_m=body.radius_m,
        weather=load_sample_weather(),
    )
