"""Compare predicted scores to the reference CSV for Lab 1."""

import sys

import pandas as pd


def main():
    prediction_file = sys.argv[1] if len(sys.argv) > 1 else "scored.csv"
    predictions = pd.read_csv(prediction_file)
    reference = pd.read_csv("data/golden_scores_v3.csv")
    required = {"transaction_id", "score"}
    for name, frame in (("reference", reference), ("predictions", predictions)):
        if not required.issubset(frame.columns):
            raise SystemExit(f"{name}: missing required columns")
        if frame.empty or frame["transaction_id"].isna().any():
            raise SystemExit(f"{name}: empty data or missing identifiers")
        if frame["transaction_id"].duplicated().any():
            raise SystemExit(f"{name}: duplicate identifiers")
        scores = pd.to_numeric(frame["score"], errors="coerce")
        if not scores.between(0, 1).all():
            raise SystemExit(f"{name}: scores must be finite probabilities")
        frame["score"] = scores
    if set(reference["transaction_id"]) != set(predictions["transaction_id"]):
        raise SystemExit("Prediction identifiers must exactly match the reference")
    compared = reference.merge(predictions, on="transaction_id",
                               suffixes=("_golden", ""), validate="one_to_one")

    wrong_rows = compared.loc[
        (compared["score"] - compared["score_golden"]).abs() > 0.000001
    ]
    matching = len(compared) - len(wrong_rows)
    print(f"{matching:,}/{len(reference):,} rows match the golden scores")

    if not wrong_rows.empty:
        print(f"SKEW: {len(wrong_rows)} rows differ. First few:")
        fields = ["transaction_id", "timestamp", "score_golden", "score"]
        print(wrong_rows[fields].head().to_string(index=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
