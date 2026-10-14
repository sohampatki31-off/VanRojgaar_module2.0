"""
The number check (PDF §11-12): before an answer is shown, every number in it must exist in his
report. One that does not means the answer is thrown away and replaced by "This is not in your
report". It runs on EVERY answer, template or AI, so a wrong figure can never reach a farmer.

A number "exists" if it is a number in the report, or that number rounded, or a distance in metres
shown in kilometres.
"""

import re
from typing import Any

from ..ask_schemas import AnswerOut
from ..schemas import ReportOut
from .ask_text import normalise

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_TOLERANCE = 1e-6


def _leaves(value: Any) -> list[float]:
    """Every number inside nested dicts and lists (booleans are not numbers)."""
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        return [n for v in value.values() for n in _leaves(v)]
    if isinstance(value, (list, tuple)):
        return [n for v in value for n in _leaves(v)]
    return []


def allowed_numbers(report: ReportOut) -> set[float]:
    """Every number the answers may use, taken from the report itself."""
    # numbers the answers COUNT (how many ideas, how many were left out) are facts about the report
    # too, so they are allowed on their own rather than by coincidence with another number
    allowed: set[float] = {
        float(n) for n in (len(report.ideas), len(report.removed), len(report.resources))
    }
    allowed.update(float(i) for i in range(1, len(report.ideas) + 1))
    for n in _leaves(report.model_dump(mode="json")):
        for digits in (0, 1, 2):
            allowed.add(round(n, digits))
        allowed.add(n)
        if n >= 100:  # metres shown as kilometres
            for digits in (0, 1, 2):
                allowed.add(round(n / 1000, digits))
    return allowed


def numbers_in_text(text: str) -> list[float]:
    """Numbers written in running text, in either digit script ("5 km", "५ किमी")."""
    return [float(m.replace(",", ".")) for m in _NUMBER.findall(normalise(text))]


def answer_numbers(answer: AnswerOut) -> list[float]:
    found = _leaves(answer.headline.params)
    for reason in answer.items:
        found += _leaves(reason.params)
    if answer.text:
        found += numbers_in_text(answer.text)
    return found


def unsupported_numbers(answer: AnswerOut, report: ReportOut) -> list[float]:
    """The numbers in the answer that are not in the report. Empty means the answer may be shown."""
    allowed = allowed_numbers(report)
    return [n for n in answer_numbers(answer) if not any(abs(n - a) <= _TOLERANCE for a in allowed)]
