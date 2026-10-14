"""
[USER RUNS - THIS SPENDS REAL MONEY] The gate for switching the AI step of "Ask about your report"
on: 30 questions in 3 languages, zero unsupported numbers (PDF section 17).

    python scripts/eval_ask_ai.py                  # dry run: what would be asked, no API call
    python scripts/eval_ask_ai.py --run            # asks the real model (needs a key, costs money)
    python scripts/eval_ask_ai.py --run --limit 6  # a small first try

It needs VANMITRA_ANTHROPIC_API_KEY (and optionally VANMITRA_LIVELIHOOD_AI_MODEL / _EFFORT) in
backend/.env or the environment. Only questions the deterministic engine cannot place reach the
model, so a full run makes far fewer calls than 90. It writes eval_out/ask_ai_eval.json
(git-ignored) with every question, the answer that would be shown and the token totals, and
exits 1 if the gate fails. Read the quality figures too: the gate only says that nothing wrong
reached a farmer.

Nothing is written to any database. The report used is the bundled SAMPLE one.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.livelihood.ai import AnthropicAnswerer  # noqa: E402
from app.livelihood.domain import ask_engine  # noqa: E402
from app.livelihood.domain.ask_eval import Case, load_cases, run_cases, summarise  # noqa: E402
from app.livelihood.domain.ask_facts import build_facts  # noqa: E402
from app.livelihood.schemas import Idea, ProfileIn, ReportOut  # noqa: E402
from app.livelihood.seed import (  # noqa: E402
    load_demo_village,
    load_ideas,
    load_sample_dataset,
    load_sample_weather,
    load_schemes,
)
from app.livelihood.service import DatasetMeta, build_report  # noqa: E402

QUESTIONS = Path(__file__).resolve().parent.parent / "tests" / "ai_eval" / "questions.json"
OUT = Path(__file__).resolve().parent.parent / "eval_out" / "ask_ai_eval.json"

PROFILE = {
    "land": {"area_value": 3, "area_unit": "acre", "land_type": "irrigated"},
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2, "goat_sheep": 5},
    "assets": ["well", "pump", "shed"],
    "past_work": ["dairy"],
    "money_level": "medium",
    "family_workers": 3,
}


def sample_report() -> ReportOut:
    header, records = load_sample_dataset()
    dataset = DatasetMeta(
        header["dataset"],
        header["data_version"],
        header["is_sample"],
        header["source"],
        header["source_date"],
    )
    return build_report(
        profile=ProfileIn.model_validate(PROFILE),
        user_name="Eval",
        village=load_demo_village(),
        resources=records,
        ideas=load_ideas(),
        dataset=dataset,
        weather=load_sample_weather(),
        schemes=load_schemes(),
    )


def model_bound(cases: list[Case], report: ReportOut, library: list[Idea]) -> list[Case]:
    """The cases whose safety check passes and that the engine leaves to the model."""
    out = []
    for c in cases:
        if ask_engine.respond(c.question, report, library).kind.value == "OFF_TOPIC":
            out.append(c)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--run", action="store_true", help="really call the model (costs money)")
    parser.add_argument("--limit", type=int, default=0, help="only the first N model-bound cases")
    args = parser.parse_args()

    settings = get_settings()
    report, library = sample_report(), load_ideas()
    cases = load_cases(QUESTIONS)
    bound = model_bound(cases, report, library)
    facts_chars = len(json.dumps(build_facts(report), ensure_ascii=False))

    print(f"questions: {len({c.id for c in cases})} x 3 languages = {len(cases)} answers")
    print(f"model-bound (the engine cannot place them): {len(bound)}")
    print(f"model: {settings.livelihood_ai_model}   effort: {settings.livelihood_ai_effort}")
    print(f"facts sent per call: about {facts_chars} characters (plus the fixed instructions)")
    if not args.run:
        print("dry run only; add --run to call the model. Check the current price first.")
        return 0

    if settings.anthropic_api_key is None:
        print("VANMITRA_ANTHROPIC_API_KEY is not set")
        return 2
    answerer = AnthropicAnswerer(settings)
    run = cases
    if args.limit:
        keep = {id(c) for c in bound[: args.limit]}
        run = [c for c in cases if id(c) in keep or id(c) not in {id(b) for b in bound}]
    results = run_cases(run, report, library, answerer)
    summary = summarise(results)
    summary["tokens"] = {
        "calls": answerer.calls,
        "input": answerer.input_tokens,
        "output": answerer.output_tokens,
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "summary": summary,
                "results": [
                    {
                        "id": r.case.id,
                        "lang": r.case.lang,
                        "question": r.case.question,
                        "kind": r.answer.kind.value,
                        "engine": r.answer.engine,
                        "text": r.answer.text,
                        "model_called": r.model_called,
                        "unsupported_numbers_in_model_words": r.raw_unsupported,
                    }
                    for r in results
                ],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"wrote {OUT}")
    print("GATE:", "PASSED" if summary["gate_passed"] else "FAILED")
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
