import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from fraud_service.logging_setup import _mask_sensitive

pytestmark = pytest.mark.unit
CHECKER = Path(__file__).resolve().parents[2] / 'scripts/check_golden.py'


def test_equivalent_timezones_have_identical_features(make_txn):
    a = make_txn(timestamp='2026-07-05T03:30:00+00:00')
    b = make_txn(timestamp='2026-07-05T06:30:00+03:00')
    assert a.to_features() == b.to_features()


def test_mask_nested_secrets():
    event = {'password': 'sentinel', 'items': [{'token': 'sentinel'}],
             'redis_url': 'redis://user:sentinel@localhost/0', 'decision': 'allow'}
    result = _mask_sensitive(None, 'info', event)
    assert 'sentinel' not in json.dumps(result)
    assert result['decision'] == 'allow'


@pytest.mark.parametrize('case', ['valid', 'missing', 'extra', 'duplicate', 'nan', 'drift'])
def test_golden_checker_rejects_incomplete_or_invalid_output(tmp_path, case):
    (tmp_path / 'data').mkdir()
    rows = [{'transaction_id': 'TXN-00001', 'score': .1, 'timestamp': 'x'},
            {'transaction_id': 'TXN-00002', 'score': .2, 'timestamp': 'y'}]
    pd.DataFrame(rows).to_csv(tmp_path / 'data/golden_scores_v3.csv', index=False)
    predicted = [{'transaction_id': r['transaction_id'], 'score': r['score']} for r in rows]
    if case == 'missing':
        predicted.pop()
    elif case == 'extra':
        predicted.append({'transaction_id': 'TXN-extra', 'score': .3})
    elif case == 'duplicate':
        predicted.append(predicted[0])
    elif case == 'nan':
        predicted[0]['score'] = float('nan')
    elif case == 'drift':
        predicted[0]['score'] = .9
    pd.DataFrame(predicted).to_csv(tmp_path / 'scored.csv', index=False)
    result = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                            capture_output=True, text=True, check=False)
    assert (result.returncode == 0) == (case == 'valid'), result.stdout + result.stderr
