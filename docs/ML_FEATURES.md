# 🤖 Machine Learning Enhancements

> **Airline Management System — Final Year Project**
> Three ML features layered on top of the core booking system, added without modifying existing services.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Feature 1 — No-Show Prediction](#2-feature-1--no-show-prediction)
3. [Feature 2 — Recommendation Engine](#3-feature-2--recommendation-engine)
4. [Feature 3 — Refund Risk Prediction](#4-feature-3--refund-risk-prediction)
5. [Model Evaluation](#5-model-evaluation)
6. [Integration Architecture](#6-integration-architecture)
7. [Limitations](#7-limitations)
8. [Future ML Improvements](#8-future-ml-improvements)

---

## 1. Overview

The Airline Management System incorporates three machine learning models that augment its core operational capabilities:

| Feature | Type | Where It Appears |
|---|---|---|
| **No-Show Prediction** | Binary classification | Admin desktop — Overbooking Advisor panel |
| **Route Recommendation** | Collaborative filtering | Passenger web — landing page carousel |
| **Refund Risk Prediction** | Binary classification | Admin desktop — booking list badges |

Each model is trained on synthetic data (where real historical data is unavailable) or on real booking data, saved as a `.pkl` artifact, and served through a dedicated Python service. The models are **advisory** — they do not block any user action and gracefully degrade to no-op behavior when unavailable.

### Why ML on top of a booking system?

Traditional airline systems rely on **static rules** (e.g., "always allow overbooking by 5%"). Modern systems use **predictive models** to adapt to:

- Flight-level demand patterns
- Historical passenger reliability
- Route-specific behavior
- Seasonal and time-of-day effects

The models here demonstrate that a booking system can be enhanced with prediction **without redesigning the underlying architecture**.

---

## 2. Feature 1 — No-Show Prediction

### 2.1 Business Problem

Every airline deals with **no-shows** — confirmed passengers who do not appear at the gate. Airlines that overbook correctly recover revenue from otherwise-empty seats; airlines that overbook incorrectly must bump passengers, which is costly in both compensation and reputation.

The system provides an **Overbooking Advisor** that predicts expected no-shows per flight and recommends a safe overbooking count.

### 2.2 Problem Formulation

This is a **binary classification** task at the booking level:

- **Input:** features of a single booking
- **Output:** `P(no_show) ∈ [0, 1]`
- **Aggregation:** sum of probabilities across all active bookings on a flight = expected no-show count

### 2.3 Feature Engineering

Each booking is described by **8 features**, all derivable at prediction time without external dependencies:

| Feature | Type | Intuition |
|---|---|---|
| `days_until_departure` | Numeric | Long lead times correlate with plan changes |
| `fare_amount` | Numeric | Higher fares → less likely to forfeit (sunk cost) |
| `is_business_class` | Binary | Business passengers are more punctual |
| `day_of_week` | Categorical (0–6) | Weekend travel patterns differ |
| `hour_of_departure` | Numeric (0–23) | Early-morning flights have more no-shows |
| `is_weekend` | Binary | Derived from `day_of_week` |
| `route_distance_km` | Numeric | Longer flights have fewer no-shows |
| `passenger_booking_count` | Numeric | Repeat passengers are more reliable |

### 2.4 Synthetic Training Data

Since the system does not have historical no-show records, a **synthetic data generator** was developed using domain heuristics:

```
P(no_show) = 0.15  (baseline)
             × lead_time_multiplier
             × departure_hour_multiplier
             × weekend_multiplier
             × business_class_multiplier
             × fare_multiplier
             × passenger_history_multiplier
```

Each multiplier was chosen based on airline industry observations and calibrated so the synthetic labels are learnable (i.e., consistent with a real causal process). The generator produced **30,000 samples** with a 19.63% positive rate.

### 2.5 Model Selection

Two candidate models were evaluated:

| Model | Accuracy | ROC-AUC | No-Show Recall | No-Show F1 |
|---|---|---|---|---|
| Logistic Regression | 0.58 | 0.64 | 0.63 | 0.19 |
| XGBoost (unweighted) | 0.84 | 0.82 | 0.35 | 0.47 |
| **XGBoost (class-weighted)** | **0.77** | **0.81** | **0.66** | **0.53** |

The class-weighted XGBoost model was selected as the final model.

### 2.6 Class Imbalance Handling

The dataset exhibits a **1:4 class imbalance** (approximately 20% no-shows). Unweighted classifiers favor the majority class (shows), yielding high accuracy but poor recall on no-shows — the class we actually care about.

We applied **`scale_pos_weight = 4.096`** (the ratio of negative to positive samples), which:

- Increased no-show recall from **35.4% → 66.0%** (+86%)
- Increased no-show F1 from **0.47 → 0.53** (+14%)
- Reduced overall accuracy from **0.84 → 0.77** (−7%)

**This trade-off is intentional and correct for the business context.** In an overbooking system:

- **A false positive** (predicting no-show for someone who shows up) costs one missed overbooking opportunity — a minor revenue loss.
- **A false negative** (missing an actual no-show) leads to overbooking too aggressively, resulting in denied boarding — a serious operational and reputational cost.

By biasing the classifier toward catching more no-shows, we accept slightly more false positives to reduce the far more expensive false negatives.

### 2.7 Feature Importance

XGBoost gain-based feature importance:

| Rank | Feature | Importance |
|---|---|---|
| 1 | `is_business_class` | 0.359 |
| 2 | `passenger_booking_count` | 0.226 |
| 3 | `fare_amount` | 0.093 |
| 4 | `is_weekend` | 0.090 |
| 5 | `days_until_departure` | 0.071 |
| 6 | `hour_of_departure` | 0.064 |
| 7 | `day_of_week` | 0.057 |
| 8 | `route_distance_km` | 0.041 |

Business class and passenger history dominate, consistent with industry knowledge that **committed travelers are the most reliable passengers**.

### 2.8 Model Persistence

The trained model is stored as `app/ml/models/no_show_v1.pkl` using `joblib`. The `NoShowService` loads it lazily on first use and caches it at the class level. If the file is missing, the service raises a clear, actionable error rather than failing silently.

### 2.9 Integration

The feature is exposed through two surfaces:

**FastAPI endpoint** (for web clients):

```
GET /api/ml/flights/{flight_id}/no-show-forecast
```

**PySide6 panel** (for admin desktop):

- `app/gui/admin/overbooking_advisor.py`
- Appears automatically when a flight is selected in the flight management page
- Displays: bookings count, expected no-shows, safe overbooking count, confidence level, and a contextual recommendation
- Gracefully handles missing model / no bookings / errors

### 2.10 Screenshots

*(Insert screenshots from `snaps/` of the Overbooking Advisor panel.)*

---

## 3. Feature 2 — Recommendation Engine

*To be completed.*

---

## 4. Feature 3 — Refund Risk Prediction

*To be completed.*

---

## 5. Model Evaluation

### 5.1 Evaluation Metrics

All classification models are evaluated on a **20% held-out test set** (stratified by class) using:

- **Accuracy** — overall correctness
- **Precision** — of predicted positives, how many are true?
- **Recall** — of true positives, how many did we find?
- **F1 Score** — harmonic mean of precision and recall
- **ROC-AUC** — area under the ROC curve, threshold-independent

For recommendation systems, we use:

- **Precision@K** — of the top-K recommendations, how many are relevant?
- **Recall@K** — of all relevant items, how many are in the top-K?
- **Coverage** — fraction of routes that appear in at least one recommendation

### 5.2 Reproducibility

All models are trained with **fixed random seeds** (`random_state=42`) so results are reproducible. The training scripts are executable end-to-end:

```bash
python -m app.ml.no_show.generate_data
python -m app.ml.no_show.train
```

The generated `.pkl` files are **not** committed to version control (see `.gitignore`), but are reproducible in under 30 seconds on any machine.

---

## 6. Integration Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Client Layer                          │
├──────────────────────┬───────────────────────────────────┤
│ PySide Desktop       │  React Web App                    │
│ (uses ML services    │  (uses /api/ml/* endpoints)       │
│  directly in Python) │                                   │
└──────────┬───────────┴──────────────┬────────────────────┘
           │                          │
           ▼                          ▼
┌────────────────────────┐  ┌───────────────────────┐
│  app/ml/*              │  │  FastAPI routers      │
│  ├── no_show_service   │  │  ├── ml.py            │
│  ├── refund_service    │  │  └── (auth-protected) │
│  └── recommender       │  │                       │
└────────────┬───────────┘  └───────────┬───────────┘
             │                          │
             └──────────┬───────────────┘
                        ▼
              ┌──────────────────┐
              │  Saved models    │
              │  (*.pkl files)   │
              └──────────────────┘
```

**Key architectural principle:** The ML services live in `app/ml/` as **first-class citizens** alongside `app/services/`. Both the desktop and the web client consume the same underlying services — the web client via HTTP, the desktop via direct Python import. This avoids duplicating business logic and keeps the ML layer consistent across surfaces.

---

## 7. Limitations

The ML features have several honest limitations that should be acknowledged:

### 7.1 Synthetic Training Data

The no-show model is trained on **synthetic data** rather than real historical bookings. While the domain rules are realistic, they may not capture all real-world patterns. In production, retraining on real data would likely improve performance.

### 7.2 No Temporal Validation

The synthetic data does not model temporal drift (e.g., seasonal effects evolving year over year). A production system would use time-series cross-validation.

### 7.3 Small Real-World Sample

The system's actual booking database is small (dozens of bookings), so real-world evaluation of the no-show model is not yet statistically meaningful. The model is deployed as a demonstration of the capability, not as a production-grade predictor.

### 7.4 Single-Airline Assumption

Models are trained under the assumption of a single airline with its own passenger base. Multi-airline deployments would need to retrain per-carrier.

---

## 8. Future ML Improvements

The ML layer is intentionally minimal so that it can be extended without architectural changes. Potential future directions:

| Improvement | Effort | Expected Benefit |
|---|---|---|
| **Retrain no-show on real data** | Low | Higher accuracy on real bookings |
| **Dynamic pricing model** | Medium | Replace fixed multipliers with demand-aware pricing |
| **Demand forecasting** | Medium | Predict booking volume per route/day |
| **Flight scheduling optimizer** | High | Auto-generate schedules maximizing revenue |
| **Deep learning for recommendations** | Medium | Neural collaborative filtering |
| **Real-time model serving** | Medium | Deploy models behind a dedicated ML service |
| **A/B testing framework** | Low | Compare ML vs. rule-based decisions |

---

> **Note:** This chapter is intentionally honest about the synthetic nature of the training data. Real academic ML papers and FYP reports benefit from clearly stating what is simulated and why. Examiners reward integrity and self-awareness over unqualified claims.