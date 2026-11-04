# app/ml/fare/generate_data.py
"""
Synthetic training data for the fare multiplier model.

The "true" multiplier is generated from domain rules:
  - Peak hours cost more
  - Weekends cost more
  - Holiday seasons cost more
  - Very-short-notice bookings cost more
  - Long-haul flights have slightly lower multipliers (fare is already higher)

Run:
    python -m app.ml.fare.generate_data
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.fare.features import FARE_FEATURE_ORDER


RANDOM_SEED = 42
N_SAMPLES = 30_000

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "fare_training.csv"


def _true_multiplier(row: dict) -> float:
    """Domain-driven 'true' multiplier used to generate labels."""
    m = 1.0

    # Peak hours
    if row["is_peak_hour"]:
        m *= 1.18

    # Weekends
    if row["is_weekend"]:
        m *= 1.22

    # Holiday season
    if row["is_holiday_season"]:
        m *= 1.38

    # Last-minute bookings
    d = row["days_until_departure"]
    if d < 1:
        m *= 1.55
    elif d < 3:
        m *= 1.30
    elif d < 7:
        m *= 1.15
    elif d > 60:
        m *= 0.90

    # Very early or very late flights → cheaper
    if row["hour_of_departure"] <= 6 or row["hour_of_departure"] >= 22:
        m *= 0.88

    # Long-haul slight reduction (base fare already high)
    if row["route_distance_km"] > 2000:
        m *= 0.92

    return round(min(max(m, 0.70), 2.50), 3)


def _random_row() -> dict:
    distance = random.choice([312, 500, 800, 1200, 1600, 2000, 2900, 3500])
    days_until = random.uniform(0, 120)

    # Pick a plausible departure datetime
    day_offset = int(days_until)
    hour = random.randint(5, 22)
    dow = random.randint(0, 6)
    month = random.randint(1, 12)

    return {
        "route_distance_km": distance,
        "days_until_departure": round(days_until, 2),
        "day_of_week": dow,
        "hour_of_departure": hour,
        "is_weekend": int(dow >= 5),
        "is_peak_hour": int(hour in (7, 8, 9, 17, 18, 19)),
        "is_holiday_season": int(month in (12, 1, 6, 7)),
        "month": month,
    }


def generate(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    rows = []
    labels = []

    for _ in range(n_samples):
        row = _random_row()
        multiplier = _true_multiplier(row)

        # Add small noise to simulate real-world variation
        noisy = multiplier * (1 + np.random.normal(0, 0.03))

        rows.append(row)
        labels.append(round(max(0.70, min(noisy, 2.50)), 3))

    df = pd.DataFrame(rows, columns=FARE_FEATURE_ORDER)
    df["multiplier"] = labels
    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {N_SAMPLES} synthetic fare samples...")
    df = generate()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✓ Wrote {len(df)} rows to {OUTPUT_FILE}")
    print(f"  Multiplier range: {df['multiplier'].min():.2f} – {df['multiplier'].max():.2f}")
    print(f"  Multiplier mean:  {df['multiplier'].mean():.3f}")
    print(f"  Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()