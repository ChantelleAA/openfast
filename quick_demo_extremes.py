#!/usr/bin/env python3
"""
Quick demo for meeting prep using currently downloaded ERA5 files.

What it does:
1) Reads downloaded monthly ERA5 files in era5_out/ (CDS zip-wrapped .nc files).
2) Builds an area-mean hourly wind speed time series at 10 m and 100 m.
3) Extrapolates to 150 m hub height from both 10 m and 100 m using the paper's
   power-law alpha=0.11.
4) Applies +10% scaling to mimic 10-min mean wind speed at hub.
5) Runs two simple EVA methods:
   - Gumbel on annual maxima
   - POT/GPD on threshold exceedances
6) Writes a markdown summary and CSV of the time series.
"""

from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import genpareto, gumbel_r


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", default="era5_out")
    p.add_argument("--output-dir", default="demo_out")
    p.add_argument("--hub-height-m", type=float, default=150.0)
    p.add_argument("--alpha", type=float, default=0.11)
    p.add_argument("--max-files", type=int, default=0, help="0 means all files")
    p.add_argument("--threshold-quantile", type=float, default=0.95)
    p.add_argument("--min-gap-hours", type=int, default=24)
    return p.parse_args()


def month_key(path: Path) -> tuple[int, int]:
    m = re.search(r"era5_sl_(\d{4})_(\d{2})\.nc$", path.name)
    if not m:
        return (9999, 99)
    return (int(m.group(1)), int(m.group(2)))


def open_month(path: Path, tmp_dir: Path) -> xr.Dataset:
    with zipfile.ZipFile(path) as zf:
        nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
        if not nc_names:
            raise RuntimeError(f"No .nc found inside {path}")
        members = []
        for name in nc_names:
            out = tmp_dir / f"{path.stem}__{Path(name).name}"
            out.write_bytes(zf.read(name))
            with xr.open_dataset(out, engine="netcdf4") as ds:
                members.append(ds.load())
    return xr.merge(members, compat="override", join="outer")


def to_series(ds: xr.Dataset, hub_height_m: float, alpha: float) -> pd.DataFrame:
    # Keep only what we need and collapse singleton metadata dimensions.
    ds = ds.squeeze(drop=True)
    if "valid_time" not in ds.coords:
        raise RuntimeError("Expected valid_time coordinate")
    needed = {"u10", "v10", "u100", "v100"}
    if not needed.issubset(set(ds.data_vars)):
        raise RuntimeError(f"Missing vars: {needed - set(ds.data_vars)}")

    ws10 = np.hypot(ds["u10"], ds["v10"])
    ws100 = np.hypot(ds["u100"], ds["v100"])
    uhub_1h_from10 = ws10 * (hub_height_m / 10.0) ** alpha
    uhub_1h_from100 = ws100 * (hub_height_m / 100.0) ** alpha
    vhub_10min_from10 = 1.10 * uhub_1h_from10
    vhub_10min_from100 = 1.10 * uhub_1h_from100

    hs = ds["swh"] if "swh" in ds.data_vars else None
    tp = ds["pp1d"] if "pp1d" in ds.data_vars else None

    # Spatial mean over requested box.
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(ds["valid_time"].values),
            "ws10_mean": ws10.mean(dim=("latitude", "longitude")).values,
            "ws100_mean": ws100.mean(dim=("latitude", "longitude")).values,
            "uhub_1h_from10_mean": uhub_1h_from10.mean(dim=("latitude", "longitude")).values,
            "uhub_1h_from100_mean": uhub_1h_from100.mean(dim=("latitude", "longitude")).values,
            "vhub_10min_from10_mean": vhub_10min_from10.mean(dim=("latitude", "longitude")).values,
            "vhub_10min_from100_mean": vhub_10min_from100.mean(dim=("latitude", "longitude")).values,
            "hs_mean": hs.mean(dim=("latitude", "longitude")).values if hs is not None else np.nan,
            "tp_mean": tp.mean(dim=("latitude", "longitude")).values if tp is not None else np.nan,
        }
    )
    df["uhub_1h_diff_mean"] = df["uhub_1h_from10_mean"] - df["uhub_1h_from100_mean"]
    df["uhub_1h_pct_diff_mean"] = 100.0 * df["uhub_1h_diff_mean"] / df["uhub_1h_from10_mean"]
    df["vhub_10min_diff_mean"] = df["vhub_10min_from10_mean"] - df["vhub_10min_from100_mean"]
    df["vhub_10min_pct_diff_mean"] = 100.0 * df["vhub_10min_diff_mean"] / df["vhub_10min_from10_mean"]
    return df


def decluster_exceedances(series: pd.Series, threshold: float, min_gap_hours: int) -> np.ndarray:
    exceed_idx = np.flatnonzero(series.values > threshold)
    if exceed_idx.size == 0:
        return np.array([])
    selected = []
    i = 0
    while i < exceed_idx.size:
        j = i
        cluster = [exceed_idx[i]]
        while j + 1 < exceed_idx.size and (exceed_idx[j + 1] - exceed_idx[j]) <= min_gap_hours:
            j += 1
            cluster.append(exceed_idx[j])
        vals = series.values[np.array(cluster)]
        selected.append(vals.max())
        i = j + 1
    return np.asarray(selected)


def gumbel_return_levels(annual_max: pd.Series, periods: list[int]) -> dict[int, float]:
    loc, scale = gumbel_r.fit(annual_max.values)
    out = {}
    for t in periods:
        p = 1.0 - 1.0 / t
        out[t] = float(gumbel_r.ppf(p, loc=loc, scale=scale))
    return out


def gpd_return_levels(series: pd.Series, periods: list[int], q: float, min_gap_hours: int) -> tuple[float, dict[int, float], int]:
    u = float(series.quantile(q))
    peaks = decluster_exceedances(series, u, min_gap_hours=min_gap_hours)
    if peaks.size < 20:
        raise RuntimeError(f"Too few peaks above threshold ({peaks.size})")
    excess = peaks - u
    c, loc, scale = genpareto.fit(excess, floc=0.0)
    years = max((series.index.max() - series.index.min()).days / 365.25, 1e-6)
    rate_per_year = peaks.size / years
    out = {}
    for t in periods:
        m = t * rate_per_year
        if abs(c) < 1e-8:
            z = u + scale * np.log(m)
        else:
            z = u + (scale / c) * (m**c - 1.0)
        out[t] = float(z)
    return u, out, int(peaks.size)


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("era5_sl_*.nc"), key=month_key)
    if args.max_files > 0:
        files = files[: args.max_files]
    if not files:
        raise SystemExit("No era5_sl_*.nc files found")

    frames: list[pd.DataFrame] = []
    with tempfile.TemporaryDirectory(prefix="era5_demo_") as tmp:
        tmp_dir = Path(tmp)
        for i, f in enumerate(files, start=1):
            try:
                frames.append(to_series(open_month(f, tmp_dir), args.hub_height_m, args.alpha))
            except Exception as exc:
                print(f"[WARN] skipping {f.name}: {exc}")
                continue
            if i % 24 == 0 or i == len(files):
                print(f"[INFO] processed {i}/{len(files)}")

    if not frames:
        raise SystemExit("No readable monthly files")

    ts = pd.concat(frames, ignore_index=True).sort_values("time").drop_duplicates(subset=["time"])
    ts = ts.set_index("time")

    annual_max_from10 = ts["vhub_10min_from10_mean"].resample("YS").max().dropna()
    annual_max_from100 = ts["vhub_10min_from100_mean"].resample("YS").max().dropna()
    periods = [50, 100]
    gumbel_rl_from10 = gumbel_return_levels(annual_max_from10, periods)
    gumbel_rl_from100 = gumbel_return_levels(annual_max_from100, periods)
    u10, gpd_rl_from10, n_peaks10 = gpd_return_levels(
        ts["vhub_10min_from10_mean"], periods, q=args.threshold_quantile, min_gap_hours=args.min_gap_hours
    )
    u100, gpd_rl_from100, n_peaks100 = gpd_return_levels(
        ts["vhub_10min_from100_mean"], periods, q=args.threshold_quantile, min_gap_hours=args.min_gap_hours
    )

    csv_path = out_dir / "demo_timeseries.csv"
    ts.to_csv(csv_path)

    abs_diff = ts["vhub_10min_diff_mean"].abs()
    pct_diff = ts["vhub_10min_pct_diff_mean"].abs()

    md_path = out_dir / "today_demo_summary.md"
    start = ts.index.min().strftime("%Y-%m-%d")
    end = ts.index.max().strftime("%Y-%m-%d")
    years = (ts.index.max() - ts.index.min()).days / 365.25
    lines = [
        "# Today Demo Results",
        "",
        "## Data Used",
        f"- Files processed: {len(files)}",
        f"- Time coverage: {start} to {end} (~{years:.1f} years)",
        "- Variables available in current files: winds (`u10`, `v10`, `u100`, `v100`) and waves (`swh`, `pp1d`) after unpacking both inner NetCDF streams.",
        "",
        "## Hub-Height Conversion (paper-consistent quick demo)",
        f"- Hub height: {args.hub_height_m:.1f} m",
        f"- Power-law exponent: alpha={args.alpha:.3f}",
        "- 10 m based conversion: `Uhub_1h_from10 = U10 * (Hhub/10)^alpha`",
        "- 100 m based conversion: `Uhub_1h_from100 = U100 * (Hhub/100)^alpha`",
        "- 10-min scaling used: `Vhub_10min = 1.10 * Uhub_1h`",
        "",
        "## Comparison of 10 m and 100 m based hub-height winds",
        f"- Mean absolute difference in `Vhub_10min`: {abs_diff.mean():.3f} m/s",
        f"- Median absolute difference in `Vhub_10min`: {abs_diff.median():.3f} m/s",
        f"- Max absolute difference in `Vhub_10min`: {abs_diff.max():.3f} m/s",
        f"- Mean absolute percent difference in `Vhub_10min`: {pct_diff.mean():.2f} %",
        "",
        "## Extreme Value Results (Area-Mean Vhub_10min)",
        f"- Annual maxima sample size (Gumbel): {len(annual_max_from10)} years",
        f"- POT threshold quantile: {args.threshold_quantile:.2f}",
        "",
        "| Series | Method | Threshold / sample | 50-year RL (m/s) | 100-year RL (m/s) |",
        "|---|---|---:|---:|---:|",
        f"| From 10 m | Gumbel (annual maxima) | {len(annual_max_from10)} years | {gumbel_rl_from10[50]:.3f} | {gumbel_rl_from10[100]:.3f} |",
        f"| From 10 m | POT/GPD | u={u10:.3f}, n={n_peaks10} | {gpd_rl_from10[50]:.3f} | {gpd_rl_from10[100]:.3f} |",
        f"| From 100 m | Gumbel (annual maxima) | {len(annual_max_from100)} years | {gumbel_rl_from100[50]:.3f} | {gumbel_rl_from100[100]:.3f} |",
        f"| From 100 m | POT/GPD | u={u100:.3f}, n={n_peaks100} | {gpd_rl_from100[50]:.3f} | {gpd_rl_from100[100]:.3f} |",
        "",
        "## Notes for Meeting",
        "- This is a quick demonstrator on the currently downloaded subset only.",
        "- The paper uses 10 m wind because its environmental model is formulated in terms of wind speed at 10 m above mean sea level.",
        "- Comparing 10 m and 100 m based extrapolations is useful as a sensitivity check on the vertical-profile assumption.",
        "- Next step is full-period completion and joint wind-wave contour work using the unpacked wave fields.",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")


if __name__ == "__main__":
    main()
