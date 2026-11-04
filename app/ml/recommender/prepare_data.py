# app/ml/recommender/prepare_data.py
"""
Prepare data for the recommendation engine.

Discovers real route IDs from the database, then generates a
synthetic user × route interaction matrix based on realistic
travel patterns.

Run:
    python -m app.ml.recommender.prepare_data
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

from app.config.database import SessionLocal
from app.models.route import Route


RANDOM_SEED = 42
N_USERS = 2_000

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "route_interactions.csv"


# ------------------------------------------------------------------
# Realistic travel patterns
# ------------------------------------------------------------------

# Popular route IDs are assigned dynamically below based on actual
# route names in the database. Any route not in this list gets weight 1.
POPULAR_ROUTE_CODES = {
    ("DAC", "CXB"): 10.0,   # Dhaka → Cox's Bazar (tourist)
    ("CGP", "DAC"):  6.0,   # Chittagong → Dhaka (commuter)
    ("DAC", "BKK"):  5.0,   # Dhaka → Bangkok (international)
    ("DAC", "CAN"):  4.0,   # Dhaka → Guangzhou
    ("DAC", "JSR"):  3.0,   # Dhaka → Jashore
    ("DAC", "SIN"):  4.0,   # Dhaka → Singapore
    ("DAC", "CXB"): 10.0,   # (duplicate key intentionally – dict keeps last)
}


def _discover_routes() -> list[int]:
    """Return all route IDs currently in the database."""
    db = SessionLocal()
    try:
        return [r.id for r in db.query(Route).all()]
    finally:
        db.close()


def _route_weights(route_ids: list[int]) -> dict[int, float]:
    """
    Compute a popularity weight for each route based on its airport codes.
    Falls back to 1.0 for routes not in POPULAR_ROUTE_CODES.
    """
    db = SessionLocal()
    try:
        weights = {}
        for r in db.query(Route).filter(Route.id.in_(route_ids)).all():
            o = r.origin_airport.iata_code if r.origin_airport else "?"
            d = r.destination_airport.iata_code if r.destination_airport else "?"
            weights[r.id] = POPULAR_ROUTE_CODES.get((o, d), 1.0)
        return weights
    finally:
        db.close()


def _sample_routes_for_user(
    rng: np.random.Generator,
    route_ids: list[int],
    weights_array: np.ndarray,
) -> list[int]:
    """Sample 1–5 routes for a user using the popularity distribution."""
    n_bookings = int(rng.integers(1, 6))

    routes = rng.choice(
        route_ids,
        size=n_bookings,
        replace=False,
        p=weights_array,
    )
    return [int(r) for r in routes]


def generate(n_users: int = N_USERS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)

    route_ids = _discover_routes()
    if not route_ids:
        raise SystemExit("No routes in database. Seed the DB first.")

    weights_map = _route_weights(route_ids)
    weights = np.array([weights_map.get(r, 1.0) for r in route_ids], dtype=float)
    weights /= weights.sum()

    print(f"Discovered {len(route_ids)} routes:")
    for r in sorted(route_ids):
        print(f"    route_id={r}  weight={weights_map.get(r, 1.0):.1f}")

    rows = []
    for user_id in range(1, n_users + 1):
        routes = _sample_routes_for_user(rng, route_ids, weights)
        for route_id in routes:
            rows.append({
                "user_id": user_id,
                "route_id": route_id,
                "count": 1,
            })

    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {N_USERS} synthetic users...")
    df = generate()
    df.to_csv(OUTPUT_FILE, index=False)

    n_users = df["user_id"].nunique()
    n_routes = df["route_id"].nunique()
    n_interactions = len(df)

    print(f"\n✓ Wrote {n_interactions} interactions to {OUTPUT_FILE}")
    print(f"  Unique users:  {n_users}")
    print(f"  Unique routes: {n_routes}")
    print(f"  Density:       {n_interactions / (n_users * n_routes):.4f}")


if __name__ == "__main__":
    main()