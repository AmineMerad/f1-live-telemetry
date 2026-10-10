"""Head-to-head prediction: baseline stub + idempotent write contract."""

from f1_common.keys import prediction_key


def running_order_baseline(prob_a_ahead: float = 0.5) -> float:
    """Current-running-order baseline. Replaced by calibrated model in week 6."""
    return prob_a_ahead


def make_prediction_record(
    session_id: str,
    driver_pair: str,
    snapshot_version: str,
    model_version: str,
    probability: float,
) -> dict:
    """Build the record persisted under the idempotency key (insert-if-absent)."""
    return {
        "prediction_key": prediction_key(
            session_id, driver_pair, snapshot_version, model_version
        ),
        "snapshot_version": snapshot_version,
        "model_version": model_version,
        "probability_a_ahead": probability,
    }
