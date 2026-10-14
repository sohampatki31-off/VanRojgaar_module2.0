"""
Write the demo report (walkthrough profile, SAMPLE data) to a JSON file, so the app can bundle a
contract-accurate report and run with no server. Files only; no database is touched.

    python scripts/export_sample_report.py ../frontend/assets/livelihood/sample_report.json
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.livelihood.schemas import ProfileIn  # noqa: E402
from app.livelihood.seed import (  # noqa: E402
    load_demo_village,
    load_ideas,
    load_sample_dataset,
    load_sample_weather,
)
from app.livelihood.service import DatasetMeta, build_report  # noqa: E402

WALKTHROUGH_PROFILE = {
    "land": {
        "area_value": 3,
        "area_unit": "acre",
        "land_type": "irrigated",
        "water_on_land": "open_well",
    },
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2, "goat_sheep": 5, "poultry": 10},
    "assets": ["well", "pump", "shed"],
    "past_work": ["millets", "dairy"],
    "family_workers": 3,
    "money_level": "medium",
}


def main(out: Path) -> None:
    header, records = load_sample_dataset()
    report = build_report(
        profile=ProfileIn.model_validate(WALKTHROUGH_PROFILE),
        user_name="Demo villager",
        village=load_demo_village(),
        resources=records,
        ideas=load_ideas(),
        dataset=DatasetMeta(
            header["dataset"],
            header["data_version"],
            header["is_sample"],
            header["source"],
            header["source_date"],
        ),
        weather=load_sample_weather(),
        report_id="sample-report",
        now=datetime(2026, 10, 14, 12, 0, tzinfo=UTC),  # fixed, so the file is reproducible
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(json.loads(report.model_dump_json()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {out} ({len(report.resources)} resources, {len(report.ideas)} ideas)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/export_sample_report.py <output.json>")
    main(Path(sys.argv[1]))
