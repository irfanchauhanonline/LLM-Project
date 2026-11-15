"""Ranking metrics. A song counts as a hit@k if ANY suitable artist is in the top k."""
from __future__ import annotations

import random


def hit_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    return 1.0 if set(ranked[:k]) & gold else 0.0


def reciprocal_rank(ranked: list[str], gold: set[str]) -> float:
    for i, aid in enumerate(ranked, start=1):
        if aid in gold:
            return 1.0 / i
    return 0.0


def summarise(per_song: list[dict]) -> dict[str, float]:
    n = len(per_song)
    return {
        "hit@1": sum(r["hit@1"] for r in per_song) / n,
        "hit@3": sum(r["hit@3"] for r in per_song) / n,
        "hit@5": sum(r["hit@5"] for r in per_song) / n,
        "mrr": sum(r["rr"] for r in per_song) / n,
        "n": n,
    }


def bootstrap_ci(values: list[float], iters: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% bootstrap interval for a mean. Small test sets are noisy; this shows how noisy."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]
