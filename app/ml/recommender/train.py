# app/ml/recommender/train.py
"""
Train the item-item collaborative filtering recommender.

Loads user × route interactions, builds a cosine similarity
matrix between routes, and saves it along with route popularity
statistics.

Run:
    python -m app.ml.recommender.train
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix


DATA_FILE = Path("data/route_interactions.csv")
MODEL_DIR = Path("app/ml/models")
MODEL_FILE = MODEL_DIR / "recommender_v1.pkl"


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Interaction data not found at {DATA_FILE}.\n"
            f"Run: python -m app.ml.recommender.prepare_data"
        )

    print(f"Loading interactions from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)

    # --- Build user × route matrix ---
    user_ids = sorted(df["user_id"].unique())
    route_ids = sorted(df["route_id"].unique())

    user_index = {uid: i for i, uid in enumerate(user_ids)}
    route_index = {rid: i for i, rid in enumerate(route_ids)}

    rows = df["user_id"].map(user_index).to_numpy()
    cols = df["route_id"].map(route_index).to_numpy()
    vals = df["count"].to_numpy()

    matrix = csr_matrix(
        (vals, (rows, cols)),
        shape=(len(user_ids), len(route_ids)),
    )

    print(f"  Matrix shape: {matrix.shape}")
    print(f"  Non-zero entries: {matrix.nnz}")
    print(f"  Density: {matrix.nnz / (matrix.shape[0] * matrix.shape[1]):.4f}")

    # --- Item-item cosine similarity ---
    # Rows = routes (transpose), then compute pairwise similarity
    print("\nComputing item-item cosine similarity...")
    route_matrix = matrix.T                     # shape: routes × users
    similarity = cosine_similarity(route_matrix)  # shape: routes × routes

    # Zero the diagonal (a route is not its own recommendation)
    np.fill_diagonal(similarity, 0)

    # --- Route popularity (fallback for cold-start) ---
    popularity = {
        int(route_ids[i]): int(matrix[:, i].sum())
        for i in range(len(route_ids))
    }
    popularity_sorted = sorted(
        popularity.items(), key=lambda x: x[1], reverse=True
    )

    # --- Save artifact ---
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "route_ids": route_ids,                     # ordered list of route IDs
        "route_index": route_index,                 # route_id → row index
        "similarity": similarity,                   # NxN matrix
        "popularity": popularity,                   # route_id → total bookings
        "popularity_sorted": popularity_sorted,     # ordered list of (route_id, count)
    }
    joblib.dump(artifact, MODEL_FILE)

    print(f"\n✓ Saved recommender to {MODEL_FILE}")
    print(f"  Routes: {len(route_ids)}")
    print(f"  Top-3 popular routes: {popularity_sorted[:3]}")


if __name__ == "__main__":
    main()