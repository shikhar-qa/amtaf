"""Semantic step matching with explicit reuse/review/generate thresholds.

The embedder here is a dependency-free bag-of-words cosine. It is deliberately
behind ``embed`` so a real embedding model + vector store (Chroma, FAISS) can
replace it without touching the decision logic.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum

from amtaf.scanner.ast_index import StepDef

REUSE_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.60

_PARAM = re.compile(r"\{[^}]*\}")
_LITERAL = re.compile(r"\"[^\"]*\"|'[^']*'|\b\d+(?:\.\d+)*\b")
_TOKEN = re.compile(r"<p>|[a-z]+")
_STOP = {"the", "a", "an", "to", "in", "on", "i", "is", "am", "of"}


class Decision(str, Enum):
    REUSE = "REUSE"
    REVIEW = "REVIEW"  # gray zone: a human should decide
    GENERATE = "GENERATE"


def embed(text: str, *, is_pattern: bool) -> Counter[str]:
    text = _PARAM.sub(" <p> ", text) if is_pattern else _LITERAL.sub(" <p> ", text)
    return Counter(t for t in _TOKEN.findall(text.lower()) if t not in _STOP)


def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(a[t] * b[t] for t in a)
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(
        sum(v * v for v in b.values())
    )
    return dot / norm if norm else 0.0


@dataclass(frozen=True)
class Match:
    text: str
    decision: Decision
    score: float
    step: StepDef | None


class StepIndex:
    def __init__(
        self,
        steps: list[StepDef],
        reuse: float = REUSE_THRESHOLD,
        review: float = REVIEW_THRESHOLD,
    ) -> None:
        self.steps = steps
        self.reuse, self.review = reuse, review
        self._vectors = [embed(s.pattern, is_pattern=True) for s in steps]

    def match(self, text: str) -> Match:
        query = embed(text, is_pattern=False)
        best, best_score = None, 0.0
        for step, vec in zip(self.steps, self._vectors):
            score = cosine(query, vec)
            if score > best_score:
                best, best_score = step, score
        if best_score >= self.reuse:
            decision = Decision.REUSE
        elif best_score >= self.review:
            decision = Decision.REVIEW
        else:
            decision = Decision.GENERATE
        return Match(text, decision, round(best_score, 2), best)
