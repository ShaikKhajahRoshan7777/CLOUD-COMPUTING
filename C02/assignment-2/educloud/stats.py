"""Small statistics helpers used by the analysis scripts."""
import math
from typing import Iterable, Sequence


def mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs)


def std(xs: Iterable[float]) -> float:
    """Sample standard deviation sqrt(sum((x-mean)^2)/(n-1)); 0 for n < 2."""
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def percentile(xs: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile (p in 0..100)."""
    s = sorted(xs)
    if not s:
        raise ValueError("empty data")
    k = (len(s) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def degradation_pct(baseline: float, measured: float) -> float:
    """Throughput degradation in % : (baseline - measured) / baseline * 100."""
    return (baseline - measured) / baseline * 100.0


def increase_pct(baseline: float, measured: float) -> float:
    """Latency increase in % : (measured - baseline) / baseline * 100."""
    return (measured - baseline) / baseline * 100.0


def ape_pct(predicted: float, measured: float) -> float:
    """Absolute percentage error |measured - predicted| / predicted * 100."""
    return abs(measured - predicted) / predicted * 100.0
