"""Recovery: worker restart resumes without duplicate prediction records.

Acceptance (week 1 demo): start RaceSessionWorkflow, restart the worker
mid-run, assert the prediction store holds exactly one record per
idempotency key. Harness TODO — runs against local Temporal.
"""


def test_idempotent_write_contract() -> None:
    from f1_prediction import make_prediction_record

    r1 = make_prediction_record("s1", "VER-NOR", "snap-42", "baseline-v0", 0.6)
    r2 = make_prediction_record("s1", "VER-NOR", "snap-42", "baseline-v0", 0.6)
    store: dict[str, dict] = {}
    store.setdefault(r1["prediction_key"], r1)
    store.setdefault(r2["prediction_key"], r2)  # retry: must not duplicate
    assert len(store) == 1
