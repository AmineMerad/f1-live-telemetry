"""Replay CLI: historical session through the pipeline (event-time order).

Fetches sessions/laps/drivers (+ optional car telemetry) for an OpenF1
session_key (cached under data/raw/openf1/), normalizes to the event
envelope, orders by source time, and prints the vertical-slice summary.
--offline replays from cache without network.
"""

import argparse
from collections import Counter
from pathlib import Path

from f1_ingestion import (
    OpenF1Auth,
    OpenF1Client,
    car_data_to_event,
    drivers_to_map,
    lap_to_event,
    session_to_event,
)

from f1_replay import order_for_replay


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a historical session")
    parser.add_argument("--session-key", required=True, help="OpenF1 session_key")
    parser.add_argument("--offline", action="store_true", help="cache only, no network")
    parser.add_argument("--cache-dir", default="data/raw/openf1")
    parser.add_argument(
        "--telemetry-driver",
        default=None,
        help="driver_number to also fetch car_data telemetry for",
    )
    args = parser.parse_args()

    client = OpenF1Client(auth=OpenF1Auth.from_env(), cache_dir=Path(args.cache_dir))
    try:
        sessions = client.get(
            "sessions", offline=args.offline, session_key=args.session_key
        )
        laps = client.get("laps", offline=args.offline, session_key=args.session_key)
        drivers = client.get(
            "drivers", offline=args.offline, session_key=args.session_key
        )
        car_rows: list[dict] = []
        if args.telemetry_driver is not None:
            car_rows = client.get(
                "car_data",
                offline=args.offline,
                session_key=args.session_key,
                driver_number=args.telemetry_driver,
            )
    finally:
        client.close()
    if not sessions:
        raise SystemExit(f"no session found for session_key={args.session_key}")
    if not laps:
        raise SystemExit(f"no laps found for session_key={args.session_key}")

    session_event = session_to_event(sessions[0])
    acronym = drivers_to_map(drivers)
    events = [lap_to_event(int(args.session_key), lap) for lap in laps]
    ordered = order_for_replay(events)
    pit_out = sum(1 for e in ordered if e.payload.get("is_pit_out_lap"))
    per_driver = Counter(e.driver_id for e in ordered)

    def name(drv: str) -> str:
        return acronym.get(drv, drv)

    print(
        f"session : {session_event.payload.get('location')} "
        f"{session_event.payload.get('session_name')}"
    )
    print(
        f"events  : {len(ordered)} laps "
        f"({pit_out} pit-out, excluded from clean-lap pace)"
    )
    print(
        f"range   : {ordered[0].source_timestamp.isoformat()} .. "
        f"{ordered[-1].source_timestamp.isoformat()}"
    )
    print(
        f"drivers : {len(per_driver)} "
        f"({', '.join(f'{name(d)}:{c}' for d, c in per_driver.most_common(5))}…)"
    )
    if car_rows:
        tel = [car_data_to_event(int(args.session_key), r) for r in car_rows]
        tel = order_for_replay(tel)
        speeds = [e.payload["speed"] for e in tel if e.payload["speed"] is not None]
        full = sum(1 for e in tel if e.payload.get("throttle") == 100)
        braking = sum(1 for e in tel if (e.payload.get("brake") or 0) > 0)
        print(
            f"telemetry: {len(tel)} samples for "
            f"{name(str(args.telemetry_driver))} "
            f"(top speed {max(speeds)} km/h, "
            f"full throttle {full / len(tel):.0%}, braking {braking / len(tel):.0%})"
        )


if __name__ == "__main__":
    main()
