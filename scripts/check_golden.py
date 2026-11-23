"""Compare predicted scores to the reference CSV for Lab 1."""

import sys

import pandas as pd


def main():
    prediction_file = sys.argv[1] if len(sys.argv) > 1 else "scored.csv"
    predictions = pd.read_csv(prediction_file)
    reference = pd.read_csv("data/golden_scores_v3.csv")
    compared = reference.merge(predictions, on="transaction_id", suffixes=("_golden", ""))

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
