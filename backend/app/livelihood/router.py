"""
Livelihood routes, mounted at /api/v1/livelihood.

Two groups:
- the real routes, which need a login and work only on the signed-in user's OWN data:
  PUT/GET/DELETE /profile (module 2); POST /report, GET /report/latest, POST /resources/nearby
  arrive in module 3 (docs/BACKEND_PLAN.md §3);
- the stateless DEMO routes: they build a report from the bundled SAMPLE dataset, store nothing
  and need no login. Switched by VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS; OFF wherever real data or
  real users are involved.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..config import get_settings
from ..errors import ApiError
from .auth import CurrentUser
from .domain.config import DEFAULT_CONFIG
from .domain.units import AreaUnit
from .geo import validate_point
from .schemas import (
    ANIMAL_CODES,
    ASSET_CODES,
    PAST_WORK_CODES,
    LocationSource,
    ProfileIn,
    ProfileOut,
    ReportOut,
    VillageRef,
)
from .seed import (
    load_demo_village,
    load_ideas,
    load_sample_dataset,
    load_sample_weather,
)
from .service import DatasetMeta, build_report
from .store import LivelihoodStore, StoredProfile, get_store

router = APIRouter(prefix="/livelihood", tags=["livelihood"])

DEMO_PLOT = {
    "lat": 19.7805,
    "lng": 73.2210,
}  # inside the sample dataset's 5 km (see seed generator)


class DemoReportRequest(BaseModel):
    profile: ProfileIn | None = None
    radius_m: int | None = None
    name: str = "Demo villager"


Store = Annotated[LivelihoodStore, Depends(get_store)]


def _profile_out(stored: StoredProfile, store: LivelihoodStore) -> ProfileOut:
    village = store.get_village(stored.village_id) if stored.village_id else None
    return ProfileOut(
        profile=stored.profile,
        area_ha=stored.profile.area_ha,
        village=(
            VillageRef(id=village.village_id, name_mr=village.name_mr, name_en=village.name_en)
            if village
            else None
        ),
        created_at=stored.created_at,
        updated_at=stored.updated_at,
    )


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: CurrentUser, store: Store) -> ProfileOut:
    """His saved details. Only ever his own: the user comes from the login, never the URL."""
    stored = store.get_profile(str(user.id))
    if stored is None:
        raise ApiError(404, "NO_PROFILE", "livelihood.no_profile")
    return _profile_out(stored, store)


@router.put("/profile", response_model=ProfileOut)
def put_profile(body: ProfileIn, user: CurrentUser, store: Store) -> ProfileOut:
    """
    Save his details, REPLACING any earlier answers. His village comes from his login (his role),
    not from the request, so he cannot file under another village.
    """
    loc = body.location
    if loc is not None and loc.source is not LocationSource.VILLAGE_CENTRE:
        try:
            validate_point(loc.lat, loc.lng)
        except ValueError as exc:
            raise ApiError(
                422, "LOCATION_OUTSIDE_MAHARASHTRA", "livelihood.location_outside_maharashtra"
            ) from exc
    stored = store.put_profile(str(user.id), user.village_id, body)
    return _profile_out(stored, store)


@router.delete("/profile", status_code=204)
def delete_profile(user: CurrentUser, store: Store) -> Response:
    """Delete his answers (rule L8). Deleting nothing is not an error: the end state is the same."""
    store.delete_profile(str(user.id))
    return Response(status_code=204)


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
