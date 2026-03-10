"""
ERA5 hourly: download 10m & 100m winds + wave variables (Hs, Tp)
from ONE dataset: reanalysis-era5-single-levels

pip install cdsapi
Ensure ~/.cdsapirc is configured.
"""

import os
import calendar
import json
import hashlib
from pathlib import Path
import cdsapi

OUTDIR = "era5_out"
os.makedirs(OUTDIR, exist_ok=True)

# [North, West, South, East]
AREA = [61.5, 0.0, 57.5, 4.0]

YEARS = list(range(1950, 2026))
MONTHS = list(range(1, 13))
TIMES = [f"{h:02d}:00" for h in range(24)]

VARS = [
    # Winds
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "100m_u_component_of_wind",
    "100m_v_component_of_wind",
    # Waves (available in single-levels)
    "significant_height_of_combined_wind_waves_and_swell",  # Hs
    "peak_wave_period",  # Tp
]

c = cdsapi.Client()

def request_payload(year: int, month: int, days: list[str]) -> dict:
    return {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": VARS,
        "year": str(year),
        "month": f"{month:02d}",
        "day": days,
        "time": TIMES,
        "area": AREA,
    }

def payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def cache_paths(target: Path) -> tuple[Path, Path]:
    return target.with_suffix(".tmp"), target.with_suffix(target.suffix + ".meta.json")

def cache_hit(target: Path, meta_path: Path, expected_hash: str) -> bool:
    if not target.exists() or not meta_path.exists():
        return False
    if target.stat().st_size == 0:
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return meta.get("request_hash") == expected_hash

def download_month(year: int, month: int):
    ndays = calendar.monthrange(year, month)[1]
    days = [f"{d:02d}" for d in range(1, ndays + 1)]
    target = Path(OUTDIR) / f"era5_sl_{year}_{month:02d}.nc"
    tmp_target, meta_path = cache_paths(target)
    payload = request_payload(year, month, days)
    req_hash = payload_hash(payload)

    if cache_hit(target, meta_path, req_hash):
        print(f"[CACHE HIT] {target}")
        return

    print(f"[GET      ] ERA5 single-levels {year}-{month:02d} -> {target}")
    c.retrieve(
        "reanalysis-era5-single-levels",
        payload,
        str(tmp_target),
    )
    os.replace(tmp_target, target)
    meta = {
        "request_hash": req_hash,
        "year": year,
        "month": month,
        "variables": VARS,
        "target_size_bytes": target.stat().st_size,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[CACHE SAVE] {target}")

if __name__ == "__main__":
    for y in YEARS:
        for m in MONTHS:
            download_month(y, m)

    print("Done.")