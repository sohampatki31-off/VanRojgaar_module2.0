"""
Build one report from plain inputs. No database and no HTTP in here: the caller hands in the
profile, the village, the resource records and the idea library, so the whole thing is testable
and the database slice only has to supply those lists.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from ..errors import ApiError
from .domain.analysis import build_analysis
from .domain.config import DEFAULT_CONFIG, LivelihoodConfig
from .domain.fit import IdeaEval, LabelledResource, evaluate_idea, idea_reason
from .domain.gates import failed_gate
from .domain.labels import label_resource
from .domain.wildlife import wildlife_risk
from .geo import centre_for, centre_inside_cfr, find_nearby
from .schemas import (
    FLOOD_KINDS,
    PROTECTED_KINDS,
    Counts,
    DisastersOut,
    FitLabel,
    Header,
    Idea,
    IdeaGroup,
    IdeaOut,
    Label,
    LocationSource,
    ProfileIn,
    Reason,
    RemovedOut,
    ReportLevel,
    ReportOut,
    ResourceOut,
    ResourceRecord,
    ToldByYou,
    TrustLabel,
    VillageGeo,
    VillageRef,
    WeatherOut,
)
from .schemas import Centre as CentreOut


@dataclass(frozen=True)
class DatasetMeta:
    name: str
    data_version: str
    is_sample: bool
    source: str
    source_date: str


def _told_by_you(profile: ProfileIn | None) -> list[ToldByYou]:
    if profile is None:
        return []
    told = [ToldByYou(kind="animal", code=c, count=n) for c, n in profile.animal_counts.items()]
    told += [ToldByYou(kind="asset", code=a) for a in profile.assets]
    return told


def _dedupe(flags: list[Reason]) -> list[Reason]:
    seen: set[tuple[str, str]] = set()
    unique: list[Reason] = []
    for flag in flags:
        marker = (flag.key, repr(sorted(flag.params.items())))
        if marker not in seen:
            seen.add(marker)
            unique.append(flag)
    return unique


def _group(ev: IdeaEval, profile: ProfileIn | None) -> IdeaGroup:
    if profile is None or not profile.has_details:
        return IdeaGroup.RANKED
    if ev.past_work_match or ev.animal_match:
        return IdeaGroup.BUILD_ON_YOUR_WORK
    return IdeaGroup.OTHER_OPTIONS


def build_report(
    *,
    profile: ProfileIn | None,
    user_name: str,
    village: VillageGeo,
    resources: Sequence[ResourceRecord],
    ideas: Sequence[Idea],
    dataset: DatasetMeta,
    cfg: LivelihoodConfig = DEFAULT_CONFIG,
    radius_m: int | None = None,
    weather: WeatherOut | None = None,
    report_id: str | None = None,
    now: datetime | None = None,
) -> ReportOut:
    radius = radius_m if radius_m is not None else cfg.default_radius_m
    if radius <= 0:
        raise ApiError(422, "INVALID_RADIUS", "livelihood.invalid_radius")
    if radius > cfg.max_radius_m:
        raise ApiError(
            422, "RADIUS_TOO_LARGE", "livelihood.radius_too_large", {"max_m": cfg.max_radius_m}
        )

    try:
        centre = centre_for(profile.location if profile else None, village)
    except ValueError as exc:
        raise ApiError(
            422, "LOCATION_OUTSIDE_MAHARASHTRA", "livelihood.location_outside_maharashtra"
        ) from exc
    level = (
        ReportLevel.VILLAGE if centre.source is LocationSource.VILLAGE_CENTRE else ReportLevel.PLOT
    )

    nearby = find_nearby(resources, centre, radius, village)
    protected = [n for n in nearby if n.record.kind in PROTECTED_KINDS]
    listed = [
        LabelledResource(n, label_resource(n.record.kind, n.record.attrs, n.distance_m, cfg))
        for n in nearby
        if n.record.kind not in PROTECTED_KINDS  # protected layers feed the wildlife check only
    ]

    protected_close = [n for n in protected if n.distance_m <= cfg.protected_near_m]
    protected_near = bool(protected_close)
    protected_nearest = (
        round(min(n.distance_m for n in protected_close)) if protected_close else None
    )
    flood_risk = any(
        n.record.kind in FLOOD_KINDS and n.distance_m <= cfg.flood_near_m for n in nearby
    )
    hot_area = bool(weather and any(m.tmax_c >= cfg.hot_month_tmax_c for m in weather.months))
    plot_in_cfr = level is ReportLevel.PLOT and centre_inside_cfr(centre, village)

    removed: list[RemovedOut] = []
    evals: list[IdeaEval] = []
    for idea in ideas:
        if not idea.enabled:
            continue
        gate = failed_gate(idea, plot_in_cfr=plot_in_cfr)
        if gate is not None:
            if idea.show_in_removed_list:
                removed.append(
                    RemovedOut(
                        code=idea.code,
                        name_mr=idea.name_mr,
                        name_en=idea.name_en,
                        gate=gate,
                        reason=Reason(key=f"gate.{gate.value.lower()}"),
                    )
                )
            continue
        evals.append(
            evaluate_idea(
                idea,
                resources=listed,
                profile=profile,
                flood_risk=flood_risk,
                hot_area=hot_area,
                protected_near=protected_near,
                cfg=cfg,
            )
        )

    # With details given, ideas that build on his own work (past work, animals) come first, best
    # fit first; a weak fit never jumps the queue. With no details it is one list by fit.
    def _priority(ev: IdeaEval) -> int:
        builds_on_work = _group(ev, profile) is IdeaGroup.BUILD_ON_YOUR_WORK
        return 0 if builds_on_work and ev.fit is not FitLabel.WEAK else 1

    evals.sort(key=lambda e: (_priority(e), -e.f, e.idea.code))
    top = evals[: cfg.top_n]
    for ev in evals[cfg.top_n :]:
        removed.append(
            RemovedOut(
                code=ev.idea.code,
                name_mr=ev.idea.name_mr,
                name_en=ev.idea.name_en,
                gate=None,
                reason=Reason(key="reason.held_back_lower_fit"),
            )
        )

    idea_cards = [
        IdeaOut(
            rank=i,
            code=ev.idea.code,
            name_mr=ev.idea.name_mr,
            name_en=ev.idea.name_en,
            group=_group(ev, profile),
            fit=ev.fit,
            reason=idea_reason(ev, cfg),
            resources_used=ev.resources_used,
            cost_level=ev.idea.cost_level,
            best_season=ev.idea.best_season,
            wildlife_risk=wildlife_risk(ev.idea, protected_near=protected_near),
            flags=_dedupe(ev.flags),
            draft=ev.idea.status != "reviewed",
        )
        for i, ev in enumerate(top, start=1)
    ]

    resource_cards = [
        ResourceOut(
            id=r.id,
            kind=r.near.record.kind,
            name_mr=r.near.record.name_mr,
            name_en=r.near.record.name_en,
            distance_m=round(r.near.distance_m),
            tag=r.near.tag,
            label=r.label.label,
            reason=r.label.reason,
            checked_on_ground=r.near.record.check_status == "confirmed",
            unknown_checks=r.label.unknown_checks,
            use_only_through_gram_sabha=r.near.tag.value == "inside_cfr",
            trust=TrustLabel(
                source=r.near.record.source,
                source_date=r.near.record.source_date,
                check_status=r.near.record.check_status,
                confidence=r.near.record.confidence,
            ),
        )
        for r in listed
    ]
    counts = Counts(
        useful=sum(r.label.label is Label.USEFUL for r in listed),
        partly_useful=sum(r.label.label is Label.PARTLY_USEFUL for r in listed),
        not_useful=sum(r.label.label is Label.NOT_USEFUL for r in listed),
        total=len(listed),
    )

    is_sample = (
        dataset.is_sample or village.is_sample or any(r.near.record.is_sample for r in listed)
    )
    analysis = build_analysis(
        profile=profile,
        resources=listed,
        ranked=top,
        protected_near=protected_near,
        protected_nearest_m=protected_nearest,
        flood_risk=flood_risk,
        report_level=level,
        is_sample=is_sample,
        radius_m=radius,
    )

    return ReportOut(
        id=report_id or uuid.uuid4().hex,
        generated_at=now or datetime.now(UTC),
        data_version=dataset.data_version,
        is_sample_data=is_sample,
        header=Header(
            name=user_name,
            village=VillageRef(
                id=village.village_id, name_mr=village.name_mr, name_en=village.name_en
            ),
            report_level=level,
            centre=CentreOut(lat=centre.lat, lng=centre.lng, source=centre.source),
            radius_m=radius,
            trust=TrustLabel(
                source=dataset.source,
                source_date=dataset.source_date,
                check_status="to_verify",
                confidence=None,
            ),
        ),
        resources=resource_cards,
        counts=counts,
        told_by_you=_told_by_you(profile),
        analysis=analysis,
        ideas=idea_cards,
        removed=removed,
        weather=weather,
        disasters=DisastersOut(is_sample=True),
    )
