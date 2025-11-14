from __future__ import annotations
import itertools
import math
import random
import statistics
from typing import List, Sequence, Tuple

QUANTILE = 0.25 # from previous year results (between first and second quantile -> peak at first Q)
STANDARD_DEV_SAMPLING = 2. # deviation of sampling starting distribution from peak QUANTILE
SAMPLE_SIZE = 10 # how many bettings
WINDOW_RADIUS = 100 # max window of betting strategy

# hard-coded, i’ve lost the code i was using to retrieve them from Sisal :(
DEFAULT_BET_PAIRS: Tuple[Tuple[str, float, float], ...] = (
    ("T/T BRESH con DE ANDRè C. - BRUNORI SAS con DIMARTINO-SINIGALLIA", 2.40, 1.50),
    ("T/T CLARA con IL VOLO - TONY EFFE con NOEMI", 1.90, 1.80),
    ("T/T COMA COSE con RIGHEIRA J. - MODà con RENGA F.", 1.47, 2.50),
    ("T/T FEDEZ con MASINI M. - OLLY con BREGOVIC G.", 1.90, 1.80),
    ("T/T FRANCESCA MICHELIN con RKOMI - FRANCESCO GABBANI con TRICARICO", 1.72, 2.00),
    ("T/T GAIA con TOQUINHO - SARAH TOSCANO con OFENBACH", 1.47, 2.50),
    ("T/T GIORGIA con ANNALISA - SIMONE CRISTICCHI con AMARA", 1.25, 3.50),
    ("T/T IRAMA con ARISA - SERENA BRANCALE con AMOROSO A.", 1.25, 3.50),
    ("T/T JOAN THIELE con FRAH QUINTALE - MARCELLA BELLA con GEMELLI LUCIA", 1.60, 2.20),
    ("T/T MASSIMO RANIERI con NERI PER CASO - ROCCO HUNT con CLEMENTINO", 1.85, 1.85),
    ("T/T ROSE VILLAIN con CHIELLO - SHABLO/GUE'/JOSHUA TORMENTO con NEFFA", 1.72, 2.00),
)

def generate_slips(pairs: Sequence[Tuple[str, float, float]]) -> List[Tuple[Tuple[int, ...], float]]:
    slips = []
    for picks in itertools.product((0, 1), repeat = len(pairs)):
        total = 1.0
        sel = []
        for __, (choice, (_, odd_a, odd_b)) in enumerate(zip(picks, pairs)):
            total *= (odd_a, odd_b)[choice]
            sel.append(choice + 1)
        slips.append((tuple(sel), total))
    slips.sort(key = lambda s: s[1])
    return slips

def summarize_quantile(slips:  List[Tuple[Tuple[int, ...], float]]):
    n = len(slips)
    return (slips[0], slips[n // 4], slips[n // 2], slips[(3 * n) // 4], slips[-1])

def describe(slip: Tuple[Tuple[int, ...], float]) -> str:
    def colorize(choice: int) -> str:
        if choice == 1:
            return f"\033[31m{choice}\033[0m"  # red for first option
        if choice == 2:
            return f"\033[34m{choice}\033[0m"  # blue for second option
        return str(choice)
    colored = ' '.join(colorize(choice) for choice in slip[0])
    return f"value = {slip[1]:.4f} -> betting = [{colored}]"

def sliding_window(values: Sequence[float], idx: int, radius: int) -> List[float]:
    l = max(0, idx - radius)
    r = min(len(values), idx + radius + 1)
    return list(values[l:r])

def local_std(values: Sequence[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else (values[0] * 0.05 if values else 0.0)

def filter_slips(slips: Sequence[Tuple[Tuple[int, ...], float]], center: float, std_mul: float, pool: Sequence[float]):
    sigma = std_mul * local_std(pool)
    sigma = sigma if sigma > 0 else max(center * 0.02, 1e-9)
    low, high = center - sigma, center + sigma
    return [s for s in slips if low <= s[1] <= high], sigma

def uniform_sample(slips: Sequence[Tuple[Tuple[int, ...], float]], k: int):
    if not slips or k <= 0:
        return []
    return random.sample(slips, k) if len(slips) >= k else random.choices(slips, k=k)

def gaussian_sample(slips: Sequence[Tuple[Tuple[int, ...], float]], center: float, sigma: float, k: int):
    if not slips or k <= 0:
        return []
    sigma = sigma if sigma > 0 else max(center * 0.05, 1e-9)
    weights = [math.exp(-0.5 * ((s[1] - center) / sigma) ** 2) for s in slips]
    return uniform_sample(slips, k) if not any(weights) else random.choices(slips, weights=weights, k=k)

def main():
    pairs = DEFAULT_BET_PAIRS
    slips = generate_slips(pairs)
    stats = summarize_quantile(slips)
    print("Betting Strategy")
    print("\n".join(f"{label.title():<4}: {describe(slip)}" for label, slip in zip(("min", "q1", "med", "q3", "max"), stats)))
    idx = min(len(slips) - 1, max(0, int(len(slips) * max(0.0, min(1.0, QUANTILE)))))
    target = slips[idx][1]
    odds = [s[1] for s in slips]
    window = sliding_window(odds, idx, WINDOW_RADIUS)
    filtered, sigma = filter_slips(slips, target, STANDARD_DEV_SAMPLING, window)
    if not filtered:
        print("\nNo slips matched the chosen range. Try a larger window or std multiplier.")
        return
    uniform = uniform_sample(filtered, SAMPLE_SIZE)
    gaussian = gaussian_sample(filtered, target, sigma / 2, SAMPLE_SIZE)
    print(f"\nFocused on idx {idx} ({QUANTILE:.2%}) odds {target:.4f}, {len(filtered)} slips in ±{sigma:.4f}.")
    print("\nUniform samples:")
    for slip in uniform:
        print(describe(slip))
    print("\nGaussian samples:")
    for slip in gaussian:
        print(describe(slip))

if __name__ == "__main__":
    main()
