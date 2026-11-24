import argparse
import csv
from collections import Counter
from pathlib import Path
from time import perf_counter

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch fraud scoring")
    parser.add_argument("--input", type=Path, default=Path("data/transactions_sample.csv"))
    parser.add_argument("--output", type=Path, default=Path("scored.csv"))
    parser.add_argument("--model", type=Path, default=Path("models/fraud_xgb_v3.joblib"))
    parser.add_argument("--threshold", type=float, default=0.85)
    args = parser.parse_args()

    start = perf_counter()
    model = SklearnModel.load(args.model)
    print(f"Loaded model fraud_xgb {model.model_version}")

    scorer = FraudScorer(model=model, block_threshold=args.threshold)
    counts: Counter[str] = Counter()

    with (
        args.input.open(newline="", encoding="utf-8") as source,
        args.output.open("w", newline="", encoding="utf-8") as target,
    ):
        writer = csv.DictWriter(
            target,
            fieldnames=["transaction_id", "score", "decision", "model_version"],
        )
        writer.writeheader()

        for row in csv.DictReader(source):
            transaction = Transaction.model_validate(row)
            result = scorer.score(transaction)

            writer.writerow({
                "transaction_id": result.transaction_id,
                "score": f"{result.probability:.9f}",
                "decision": result.decision.value,
                "model_version": result.model_version,
            })
            counts[result.decision.value] += 1

    total = sum(counts.values())
    print(f"Scored {total:,} transactions in {perf_counter() - start:.2f}s")
    print(f"Decisions: {dict(counts)}")
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
