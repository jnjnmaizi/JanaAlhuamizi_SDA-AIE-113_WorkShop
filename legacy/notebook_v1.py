"""Legacy transaction scorer for Lab 1. Intentionally contains a feature bug."""

import math
import os

import joblib
import pandas as pd

# This legacy style loads external resources as soon as the module is imported.
transactions = pd.read_csv("data/transactions_sample.csv")
model = joblib.load("models/fraud_xgb_v3.joblib")["pipeline"]
output_rows = []


def training_check_features(row):
    """Reference-like feature mapping, retained for the lab comparison."""
    hour = pd.to_datetime(row["timestamp"]).hour
    return {
        "amount_log": round(math.log1p(row["amount_sar"]), 6),
        "channel": row["channel"],
        "mcc": row["merchant_category"],
        "hour_of_day": hour,
        "is_night": int(hour < 6),
    }


def run_scoring():
    threshold = float(os.getenv("THRESHOLD", "0.85"))
    for row in transactions.to_dict(orient="records"):
        try:
            hour = int(row["timestamp"].split("T")[1][:2])
            model_input = pd.DataFrame([{
                "amount_log": round(math.log1p(row["amount_sar"]), 6),
                "channel": row["channel"],
                "mcc": row["merchant_category"],
                "hour_of_day": hour,
                "is_night": int(hour <= 6),  # Intentional training/serving skew.
            }])
            probability = float(model.predict_proba(model_input)[0, 1])
        except Exception:
            probability = 0.0  # Intentionally unsafe legacy error handling.

        review_band = float(os.getenv("REVIEW_BAND", "0.15"))
        if probability >= threshold:
            decision = "block"
        elif probability >= threshold - review_band:
            decision = "review"
        else:
            decision = "allow"

        output_rows.append({
            "transaction_id": row["transaction_id"],
            "score": probability,
            "decision": decision,
        })

    scored = pd.DataFrame(output_rows)
    scored.to_csv("scored_notebook.csv", index=False)
    print(scored["decision"].value_counts().to_dict())


if __name__ == "__main__":
    run_scoring()
