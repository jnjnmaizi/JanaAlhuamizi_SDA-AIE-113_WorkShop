"""Starter assets for SDA-AIE-113. Run once from the repo root:

    python scripts/make_course_assets.py

Creates, deterministically (same seed -> same files):
  data/transactions_sample.csv   5,000 synthetic card transactions (SAR)
  models/fraud_xgb_v3.joblib     trained gradient-boosting pipeline + its version
  data/golden_scores_v3.csv      reference score for every row (the skew tripwire)
  payloads/sample.json           one valid request body
  payloads/malformed/*.json      40 bad requests the API must reject
  src/fraud_service/...          empty package folders for the layers you will fill
"""
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SEED, N, VERSION = 113, 5000, "v3.2.0"
CHANNELS = ["pos", "ecom", "atm", "transfer"]
MCCS = ["GROCERY", "ELECTRONICS", "FUEL", "RESTAURANT",
        "TRAVEL", "JEWELRY", "PHARMACY", "TELECOM"]


def make_transactions(rng: np.random.Generator) -> pd.DataFrame:
    seconds = rng.integers(0, 30 * 24 * 3600, N)
    ts = pd.Timestamp("2026-07-01", tz="UTC") + pd.to_timedelta(seconds, unit="s")
    df = pd.DataFrame({
        "transaction_id": [f"TXN-2026-{i:05d}" for i in range(N)],
        "amount_sar": np.round(rng.lognormal(5.0, 1.3, N).clip(1, 250_000), 2),
        "channel": rng.choice(CHANNELS, N, p=[0.45, 0.35, 0.10, 0.10]),
        "merchant_category": rng.choice(MCCS, N),
        "customer_id": [f"CUST-{c:05d}" for c in rng.integers(1, 1500, N)],
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    })
    risk = (-6.0 + 0.62 * np.log1p(df["amount_sar"]) + 1.3 * (ts.hour < 6)
            + 1.0 * df["channel"].isin(["ecom", "transfer"])
            + 0.9 * df["merchant_category"].isin(["JEWELRY", "ELECTRONICS"]))
    df["is_fraud"] = (rng.random(N) < 1 / (1 + np.exp(-risk))).astype(int)
    return df


def training_features(df: pd.DataFrame) -> pd.DataFrame:
    """The data-science team's feature logic. Serving must reproduce it exactly."""
    hour = pd.to_datetime(df["timestamp"]).dt.hour
    return pd.DataFrame({
        "amount_log": df["amount_sar"].map(lambda a: round(math.log1p(a), 6)),
        "channel": df["channel"],
        "mcc": df["merchant_category"],
        "hour_of_day": hour,
        "is_night": (hour < 6).astype(int),
    })


def train(df: pd.DataFrame) -> Pipeline:
    prep = ColumnTransformer([
        ("num", "passthrough", ["amount_log", "hour_of_day", "is_night"]),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
         ["channel", "mcc"]),
    ])
    n_cols = 3 + len(CHANNELS) + len(MCCS)
    clf = HistGradientBoostingClassifier(
        max_iter=60, learning_rate=0.1, random_state=SEED,
        monotonic_cst=[1] + [0] * (n_cols - 1),   # risk never falls as amount rises
    )
    return Pipeline([("prep", prep), ("clf", clf)]).fit(training_features(df), df["is_fraud"])


def make_payloads(root: Path) -> int:
    good = {"transaction_id": "TXN-2026-00042", "amount_sar": 249.99, "channel": "ecom",
            "merchant_category": "electronics", "customer_id": "CUST-00077",
            "timestamp": "2026-07-05T03:30:00+00:00"}
    bad: dict[str, object] = {f"missing_{k}": {a: b for a, b in good.items() if a != k}
                              for k in good}
    bad |= {f"null_{k}": {**good, k: None} for k in good}
    bad |= {
        "amount_negative": {**good, "amount_sar": -1},
        "amount_zero": {**good, "amount_sar": 0},
        "amount_too_large": {**good, "amount_sar": 5_000_000},
        "amount_text": {**good, "amount_sar": "a lot"},
        "amount_list": {**good, "amount_sar": [100]},
        "amount_object": {**good, "amount_sar": {"value": 100}},
        "typo_amount_sr": {("amount_sr" if k == "amount_sar" else k): v for k, v in good.items()},
        "unknown_field_is_admin": {**good, "is_admin": True},
        "unknown_field_debug": {**good, "debug": {"dump_features": True}},
        "channel_unknown": {**good, "channel": "telepathy"},
        "channel_uppercase": {**good, "channel": "ECOM"},
        "channel_sql": {**good, "channel": "pos'; DROP TABLE txns;--"},
        "channel_number": {**good, "channel": 3},
        "transaction_id_short": {**good, "transaction_id": "T1"},
        "transaction_id_long": {**good, "transaction_id": "T" * 500},
        "transaction_id_number": {**good, "transaction_id": 2026000042},
        "customer_id_short": {**good, "customer_id": "C"},
        "customer_id_long": {**good, "customer_id": "C" * 500},
        "customer_id_number": {**good, "customer_id": 77},
        "mcc_short": {**good, "merchant_category": "X"},
        "mcc_long": {**good, "merchant_category": "M" * 300},
        "mcc_number": {**good, "merchant_category": 5411},
        "timestamp_ddmmyyyy": {**good, "timestamp": "05/07/2026"},
        "timestamp_text": {**good, "timestamp": "yesterday at night"},
        "empty_object": {},
        "top_level_array": [good],
        "top_level_string": "score this please",
    }
    out = root / "malformed"
    out.mkdir(parents=True, exist_ok=True)
    for name, body in bad.items():
        (out / f"{name}.json").write_text(json.dumps(body, indent=1), encoding="utf-8")
    (out / "not_json.json").write_text('{amount_sar: 100, "channel": ', encoding="utf-8")
    (root / "sample.json").write_text(json.dumps(good, indent=1), encoding="utf-8")
    return len(bad) + 1


def make_skeleton() -> None:
    packages = ["src/fraud_service"] + [f"src/fraud_service/{layer}" for layer in
                                        ("domain", "service", "adapters", "api")]
    packages += ["tests", "tests/unit", "tests/integration", "tests/behavioural"]
    for pkg in packages:
        Path(pkg).mkdir(parents=True, exist_ok=True)
        (Path(pkg) / "__init__.py").touch()


def main() -> None:
    for d in ("data", "models", "payloads"):
        Path(d).mkdir(exist_ok=True)
    make_skeleton()
    df = make_transactions(np.random.default_rng(SEED))
    df.to_csv("data/transactions_sample.csv", index=False)

    pipeline = train(df)
    joblib.dump({"pipeline": pipeline, "version": VERSION}, "models/fraud_xgb_v3.joblib")

    golden = df.rename(columns={"merchant_category": "mcc"}).drop(columns="is_fraud")
    golden["score"] = pipeline.predict_proba(training_features(df))[:, 1].round(9)
    golden.to_csv("data/golden_scores_v3.csv", index=False)

    n_bad = make_payloads(Path("payloads"))
    size_kb = Path("models/fraud_xgb_v3.joblib").stat().st_size / 1024
    print(f"transactions : {len(df):,} rows, fraud rate {df['is_fraud'].mean():.1%}")
    print(f"model        : fraud_xgb {VERSION} ({size_kb:.0f} KB)")
    print(f"golden scores: {len(golden):,} rows  (>=0.85: {(golden['score'] >= 0.85).sum()},"
          f" 0.70-0.85: {((golden['score'] >= 0.70) & (golden['score'] < 0.85)).sum()})")
    print(f"payloads     : 1 valid, {n_bad} malformed")
    print("skeleton     : src/fraud_service/{domain,service,adapters,api} and tests/ ready")


if __name__ == "__main__":
    main()
