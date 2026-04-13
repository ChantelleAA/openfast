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
import zipfile
from pathlib import Path
import cdsapi

OUTDIR = "era5_out"
os.makedirs(OUTDIR, exist_ok=True)

# [North, West, South, East]
AREA = [62.0, -18.0, 48.0, 5.0]

YEARS = [1950] + list(range(2001, 2026))
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

def extracted_paths(stem: str, outdir: Path) -> tuple[Path, Path]:
    return outdir / f"{stem}_oper.nc", outdir / f"{stem}_wave.nc"

def extract_zip(zip_path: Path):
    stem = zip_path.stem  # e.g. "era5_sl_1950_01"
    oper_out, wave_out = extracted_paths(stem, zip_path.parent)
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            dest = oper_out if "oper" in name else wave_out
            with zf.open(name) as src, open(dest, "wb") as dst:
                dst.write(src.read())
    print(f"[UNZIP    ] {zip_path.name} -> {oper_out.name}, {wave_out.name}")

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
    stem = f"era5_sl_{year}_{month:02d}"
    target = Path(OUTDIR) / f"{stem}.nc"
    tmp_target, meta_path = cache_paths(target)
    payload = request_payload(year, month, days)
    req_hash = payload_hash(payload)

    oper_out, wave_out = extracted_paths(stem, Path(OUTDIR))
    if cache_hit(target, meta_path, req_hash) and oper_out.exists() and wave_out.exists():
        print(f"[CACHE HIT] {target}")
        return

    print(f"[GET      ] ERA5 single-levels {year}-{month:02d} -> {target}")
    c.retrieve(
        "reanalysis-era5-single-levels",
        payload,
        str(tmp_target),
    )
    os.replace(tmp_target, target)
    extract_zip(target)
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