"""Fuzzy name matching (rapidfuzz when installed, difflib otherwise)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from .textutils import normalize_name

try:  # rapidfuzz is the intended engine (see requirements.txt)
    from rapidfuzz import fuzz as _fuzz

    def similarity(a: str, b: str) -> float:
        return float(_fuzz.token_sort_ratio(a, b))

except ImportError:  # pure-Python fallback so the engine still runs without it
    from difflib import SequenceMatcher

    def similarity(a: str, b: str) -> float:
        ta, tb = " ".join(sorted(a.split())), " ".join(sorted(b.split()))
        if not ta or not tb:
            return 0.0
        sm = SequenceMatcher(None, ta, tb, autojunk=False)
        if sm.real_quick_ratio() < 0.4 or sm.quick_ratio() < 0.4:
            return 0.0
        return 100.0 * sm.ratio()


def _numbers(norm: str) -> set[str]:
    return {t for t in norm.split() if any(c.isdigit() for c in t)}


def pair_score(a_norm: str, b_norm: str) -> float:
    """Similarity of two normalised names, with a guard on numbers.

    '650mg' vs '500mg' (or '2 views' vs '3 views') are different items even
    though the text is almost identical, so conflicting numbers never match.
    """
    if a_norm == b_norm:
        return 100.0
    score = similarity(a_norm, b_norm)
    na, nb = _numbers(a_norm), _numbers(b_norm)
    if na and nb and na != nb:
        return min(score, 50.0)
    if bool(na) != bool(nb):
        score -= 5.0
    return score


@dataclass
class Candidate:
    entry: Any
    score: float


class NameIndex:
    """Scores a bill description against every reference entry (and its aliases)."""

    def __init__(self, entries: Sequence[Any], names_of: Callable[[Any], Iterable[str]]):
        self._rows = [
            (e, [n for n in (normalize_name(x) for x in names_of(e)) if n]) for e in entries
        ]

    def top(self, description: str, n: int = 5, floor: float = 0.0) -> list[Candidate]:
        norm = normalize_name(description)
        if not norm:
            return []
        out: list[Candidate] = []
        for entry, names in self._rows:
            best = max((pair_score(norm, name) for name in names), default=0.0)
            if best >= floor:
                out.append(Candidate(entry, best))
        out.sort(key=lambda c: c.score, reverse=True)
        return out[:n]
