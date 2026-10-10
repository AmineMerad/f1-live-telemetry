"""Head-to-head plots from OpenF1 data (thin wrapper over f1_intelligence).

Usage:
    uv run python scripts/plot_session.py --session-key 9590 --pair VER-NOR
Output: data/figures/9590_VER-NOR_laps.png, ..._speed.png
"""

import argparse
from pathlib import Path

from f1_ingestion import OpenF1Auth, OpenF1Client, drivers_to_map
from f1_intelligence import clean_laps_by_code, lap_progression_png, speed_trace_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot head-to-head session data")
    parser.add_argument("--session-key", default="9590")
    parser.add_argument("--pair", default="VER-NOR", help="ACRONYM-ACRONYM")
    parser.add_argument("--cache-dir", default="data/raw/openf1")
    parser.add_argument("--out-dir", default="data/figures")
    args = parser.parse_args()
    a_code, b_code = args.pair.split("-")

    client = OpenF1Client(auth=OpenF1Auth.from_env(), cache_dir=Path(args.cache_dir))
    try:
        laps = client.get("laps", session_key=args.session_key)
        drivers = client.get("drivers", session_key=args.session_key)
        num_by_code = {c: n for n, c in drivers_to_map(drivers).items()
                       if c in (a_code, b_code)}
        _, fastest = clean_laps_by_code(laps, num_by_code)
        car_by_code = {
            code: client.get(
                "car_data", session_key=args.session_key, driver_number=num
            )
            for code, num in num_by_code.items()
        }
    finally:
        client.close()

    for code in (a_code, b_code):
        lap = fastest[code]
        print(f"{code}: fastest clean lap {lap['lap_number']} ({lap['lap_duration']:.3f}s)")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tag = f"{args.session_key}_{args.pair}"
    laps_path = out / f"{tag}_laps.png"
    speed_path = out / f"{tag}_speed.png"
    laps_path.write_bytes(lap_progression_png(laps, num_by_code, args.session_key, args.pair))
    speed_path.write_bytes(speed_trace_png(car_by_code, fastest, args.pair))
    print(f"saved {laps_path}\nsaved {speed_path}")


if __name__ == "__main__":
    main()
