from __future__ import annotations

import random


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, identifier in enumerate(retrieved, start=1):
        if identifier in relevant:
            return 1.0 / rank
    return 0.0


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def bootstrap_mean_ci(
    values: list[float], confidence: float = 0.95, samples: int = 2000, seed: int = 42
) -> tuple[float, float] | None:
    """Return a deterministic percentile bootstrap interval for a macro mean."""
    if not values:
        return None
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(seed)
    sample_means = sorted(
        sum(rng.choice(values) for _ in values) / len(values) for _ in range(samples)
    )
    tail = (1.0 - confidence) / 2.0
    lower = sample_means[max(0, int(tail * samples))]
    upper = sample_means[min(samples - 1, int((1.0 - tail) * samples) - 1)]
    return lower, upper


def metric_summary(values: list[float], digits: int = 4) -> dict:
    average = mean(values)
    interval = bootstrap_mean_ci(values)
    return {
        "value": round(average, digits) if average is not None else None,
        "ci95": [round(interval[0], digits), round(interval[1], digits)] if interval else None,
        "samples": len(values),
    }
