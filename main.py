from __future__ import annotations
import itertools
import json
import math
import os
import random
import statistics
from typing import List, Sequence, Tuple, Dict
from util import get_matches

SAMPLING_METHOD = "Gaussian" # or "Uniform" -> Distribution form sampling with peak quartile, default Gaussian
SORT_BY_PRODUCT = False # product sort tuples (from higher Q1 * Q2 to lower) effective only when SAMPLE_SIZE < Actual Match Size
QUANTILE = 0.25 # from previous year results (between first and second quantile -> peak at first Q)
SAMPLE_SIZE = 14 # how many bettings

# if you have it insert it, a sample of structure is this, if None, auto retrieval do the trick
# ( ("T/T BRESH con DE ANDRè C. - BRUNORI SAS con DIMARTINO-SINIGALLIA", 2.40, 1.50), ..., ..., )
DEFAULT_BET_PAIRS: Tuple[Tuple[str, float, float], ...] | None = None

def get_top_k_pairs(matches: List[Dict], k: int = SAMPLE_SIZE, sort: bool = SORT_BY_PRODUCT) -> Tuple[Tuple[str, float, float], ...]:
    processed_list = []
    for m in matches:
        full_title = f"T/T {m['sfidante_1']} - {m['sfidante_2']}"
        q1 = m['quota_1']
        q2 = m['quota_2']
        product = q1 * q2
        entry = (full_title, q1, q2)
        processed_list.append((product, entry))
    if sort:
        processed_list.sort(key = lambda x: x[0], reverse = True)
    top_k = [item[1] for item in processed_list[:k]]
    return tuple(top_k)

def load_matches_from_disk(filename: str) -> Tuple[Tuple[str, float, float], ...]:
    if not os.path.exists(filename):
        return ()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return get_top_k_pairs(data)
    except json.JSONDecodeError:
        return ()
    except Exception as _:
        return ()

def save_slips_to_file(filename: str, slips: Sequence[Tuple[Tuple[int, ...], float]], pairs: Sequence[Tuple[str, float, float]], infos: str = ""):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"SANREMO BETTING REPORT\n")
            if infos != "":
                f.write(f"{infos}\n")
            f.write(f"Sampling method: {SAMPLING_METHOD} | Quantile Target: {QUANTILE}\n")
            f.write("="*60 + "\n\n")
            for i, (picks, total_odd) in enumerate(slips, 1):
                f.write(f"--- BET #{i} (Total multiplier bet: {total_odd:.2f}) ---\n")
                for idx_match, (choice, pair_data) in enumerate(zip(picks, pairs)):
                    title = pair_data[0].replace("T/T ", "")
                    bet = pair_data[choice]
                    whos = title.split(" - ")
                    if len(whos) == 2:
                        name = whos[choice - 1]
                    else:
                        name = f"Esito {choice}"
                    f.write(f"{idx_match+1:02}. {title}\n")
                    f.write(f"    BET ON: {name} (@ {bet:.2f})\n")                
                f.write("\n" + "-"*30 + "\n\n")
    except Exception as _:
        print(f"I/O Error")

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
            return f"\033[31m{choice}\033[0m"
        if choice == 2:
            return f"\033[34m{choice}\033[0m"
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
    if pairs is None:
        pairs = load_matches_from_disk("quote_sanremo_TT.json")
        if pairs == ():
            pairs = get_top_k_pairs(get_matches(), k = SAMPLE_SIZE, sort = SORT_BY_PRODUCT)
    slips = generate_slips(pairs)
    stats = summarize_quantile(slips)
    # Calculate total phase space (2^N combinations)
    total_combinations = 2 ** len(pairs)
    # Window Radius: 1/8 of the total (12.5%). 
    # Wide enough to capture the gradient towards adjacent quantiles.
    WINDOW_RADIUS = int(total_combinations / 8)
    # Filter Standard Deviation: Very wide (4.0).
    # Used to avoid clipping the Gaussian tails before sampling.
    STANDARD_DEV_SAMPLING = 4.0
    params_comment = f"""Dynamic Strategy on {len(pairs)} matches ({total_combinations} total slips).\nCalculated Parameters: Window Radius = {WINDOW_RADIUS}, StdDev Filter = {STANDARD_DEV_SAMPLING}.\nDistribution Target: ~60% slips near quantile {QUANTILE}, ~40% on tails (towards adjacent quantiles)."""
    print(params_comment)
    print("\n".join(f"{label.title():<4}: {describe(slip)}" for label, slip in zip(("min", "q1", "med", "q3", "max"), stats)))
    idx = min(len(slips) - 1, max(0, int(len(slips) * max(0.0, min(1.0, QUANTILE)))))
    target = slips[idx][1]
    odds = [s[1] for s in slips]
    window = sliding_window(odds, idx, WINDOW_RADIUS)
    filtered, sigma = filter_slips(slips, target, STANDARD_DEV_SAMPLING, window)
    if not filtered:
        print("\nNo slips matched the chosen range. Try a larger window or std multiplier.")
        return
    sample = ()
    if SAMPLING_METHOD == "Gaussian":
        sample = gaussian_sample(filtered, target, sigma, SAMPLE_SIZE)
    elif SAMPLING_METHOD == "Uniform":
        sample = uniform_sample(filtered, SAMPLE_SIZE)
    print(f"\nFocused on idx {idx} ({QUANTILE:.2%}) odds {target:.4f}, {len(filtered)} slips in ±{sigma:.4f}.")
    print(f"\n{SAMPLING_METHOD} samples:")
    for slip in sample:
        print(describe(slip))
    save_slips_to_file("betting_strategy.txt", sample, pairs, params_comment)

if __name__ == "__main__":
    main()