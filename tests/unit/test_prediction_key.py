"""Unit: prediction keys are stable — retries reuse the captured snapshot."""

from f1_common.keys import prediction_key
from f1_prediction import make_prediction_record


def test_prediction_key_deterministic() -> None:
    k1 = prediction_key("s1", "VER-NOR", "snap-42", "baseline-v0")
    k2 = prediction_key("s1", "VER-NOR", "snap-42", "baseline-v0")
    assert k1 == k2 == "s1:VER-NOR:snap-42:baseline-v0"


def test_prediction_record_carries_versions() -> None:
    rec = make_prediction_record("s1", "VER-NOR", "snap-42", "baseline-v0", 0.6)
    assert rec["prediction_key"] == "s1:VER-NOR:snap-42:baseline-v0"
    assert rec["probability_a_ahead"] == 0.6
