# app/ml/no_show/generate_data.py
"""
Synthetic training data generator for no-show prediction.

Since the FYP system does not yet have enough real historical no-show
records, we generate realistic synthetic data using domain heuristics
(short lead time, early morning, weekend, low fare → higher no-show risk).

Run:
    python -m app.ml.no_show.generate_data
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.features import NO_SHOW_FEATURE_ORDER


RANDOM_SEED = 42
N_SAMPLES = 30_000

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "no_show_training.csv"


def _simulate_no_show_probability(row: dict) -> float:
    """
    Domain-driven probability of a no-show.

    Real airlines observe:
      - Long lead time        → more likely to no-show (plans change)
      - Early morning flights → more likely to no-show (oversleep)
      - Weekend flights       → slightly more likely
      - Business class        → much less likely to no-show
      - High fare             → less likely to no-show (sunk cost)
      - Repeat passengers     → less likely to no-show (they travel often)

    Multipliers are strong so the classifier can learn clean decision
    boundaries (this is intentional: the "true" causal effects in
    airline no-show behavior are large).
    """
    p = 0.15   # baseline

    # Lead time
    if row["lead_time_hours"] > 60 * 24:
        p *= 3.5
    elif row["lead_time_hours"] > 30 * 24:
        p *= 2.2
    elif row["lead_time_hours"] > 14 * 24:
        p *= 1.4
    elif row["lead_time_hours"] < 24:
        p *= 0.35

    # Departure hour
    if row["hour_of_departure"] < 7:
        p *= 2.5
    elif row["hour_of_departure"] < 9:
        p *= 1.5
    elif row["hour_of_departure"] >= 20:
        p *= 1.4

    # Weekend
    if row["is_weekend"]:
        p *= 1.6

    # Business class
    if row["is_business_class"]:
        p *= 0.25

    # Fare
    if row["fare_amount"] > 200:
        p *= 0.35
    elif row["fare_amount"] > 100:
        p *= 0.55
    elif row["fare_amount"] < 40:
        p *= 1.5

    # Repeat passengers
    if row["passenger_booking_count"] >= 5:
        p *= 0.25
    elif row["passenger_booking_count"] >= 2:
        p *= 0.55
    elif row["passenger_booking_count"] == 0:
        p *= 1.4

    return min(max(p, 0.02), 0.95)


def _random_row() -> dict:
    """Generate one synthetic booking feature row."""
    days_until = random.uniform(0, 90)
    lead_time_hours = days_until * 24 + random.gauss(0, 6)
    lead_time_hours = max(1.0, lead_time_hours)

    fare_amount = round(random.uniform(25, 400), 2)
    is_business = random.choices([0, 1], weights=[0.85, 0.15])[0]
    if is_business:
        fare_amount = round(fare_amount * 2.5, 2)

    day_of_week = random.randint(0, 6)
    hour_of_departure = random.randint(5, 22)
    is_weekend = int(day_of_week >= 5)
    route_distance_km = random.choice([312, 500, 800, 1200, 2000, 3000])
    passenger_booking_count = random.choices(
        [0, 1, 2, 3, 5, 10, 20],
        weights=[0.30, 0.20, 0.15, 0.10, 0.12, 0.08, 0.05],
    )[0]

    return {
        "days_until_departure": round(days_until, 2),
        "lead_time_hours": round(lead_time_hours, 2),
        "fare_amount": fare_amount,
        "is_business_class": is_business,
        "day_of_week": day_of_week,
        "hour_of_departure": hour_of_departure,
        "is_weekend": is_weekend,
        "route_distance_km": route_distance_km,
        "passenger_booking_count": passenger_booking_count,
    }


def generate(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    rows = []
    labels = []

    for _ in range(n_samples):
        row = _random_row()
        p = _simulate_no_show_probability(row)
        label = int(np.random.rand() < p)
        rows.append(row)
        labels.append(label)

    df = pd.DataFrame(rows, columns=NO_SHOW_FEATURE_ORDER)
    df["no_show"] = labels
    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {N_SAMPLES} synthetic no-show samples...")
    df = generate()
    df.to_csv(OUTPUT_FILE, index=False)

    rate = df["no_show"].mean()
    print(f"✓ Wrote {len(df)} rows to {OUTPUT_FILE}")
    print(f"  No-show rate: {rate:.2%}")
    print(f"  Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()