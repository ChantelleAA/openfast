#!/usr/bin/env python3
"""
Compare multiple extreme-value methods on the quick demo time series.

Inputs:
- demo_out/demo_timeseries.csv (from quick_demo_extremes.py)

Outputs:
- demo_out/method_comparison.csv
- demo_out/fig_timeseries_vhub_compare.png
- demo_out/fig_monthly_mean_vhub_compare.png
- demo_out/fig_monthly_mean_ws100_validation.png
- demo_out/fig_annual_maxima_compare.png
- demo_out/fig_extrapolation_gap.png
- demo_out/fig_extrapolation_means_bar.png
- demo_out/fig_alpha_sensitivity.png
- demo_out/fig_pot_mrl.png
- demo_out/fig_return_levels.png
- demo_out/method_interpretation.md
- demo_out/extrapolation_notes.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import genextreme, genpareto, gumbel_r, lognorm, weibull_min


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-csv", default="demo_out/demo_timeseries.csv")
    p.add_argument("--output-dir", default="demo_out")
    p.add_argument("--threshold-quantile", type=float, default=0.95)
    p.add_argument("--min-gap-hours", type=int, default=24)
    p.add_argument(
        "--target-column",
        default="vhub_10min_from10_mean",
        choices=["vhub_10min_from10_mean", "vhub_10min_from100_mean"],
    )
    return p.parse_args()


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


def rl_from_gpd(
    series: pd.Series, threshold: float, periods: list[int], min_gap_hours: int
) -> tuple[dict[int, float], int, tuple[float, float]]:
    peaks = decluster_exceedances(series, threshold, min_gap_hours=min_gap_hours)
    excess = peaks - threshold
    c, loc, scale = genpareto.fit(excess, floc=0.0)
    years = max((series.index.max() - series.index.min()).days / 365.25, 1e-6)
    rate_per_year = peaks.size / years
    out = {}
    for t in periods:
        m = t * rate_per_year
        if abs(c) < 1e-8:
            z = threshold + scale * np.log(m)
        else:
            z = threshold + (scale / c) * (m**c - 1.0)
        out[t] = float(z)
    return out, int(peaks.size), (float(c), float(scale))


def mrl_curve(series: pd.Series, q_low: float = 0.85, q_high: float = 0.99, n: int = 25) -> pd.DataFrame:
    qs = np.linspace(q_low, q_high, n)
    rows = []
    for q in qs:
        u = float(series.quantile(q))
        ex = series[series > u] - u
        if len(ex) < 20:
            continue
        rows.append({"q": q, "u": u, "mrl": float(ex.mean()), "n_exc": int(len(ex))})
    return pd.DataFrame(rows)


def fit_block_max_methods(annual_max: pd.Series, periods: list[int]) -> dict[str, dict[int, float]]:
    x = annual_max.values
    out: dict[str, dict[int, float]] = {}

    # 1) Gumbel
    loc, scale = gumbel_r.fit(x)
    out["Gumbel_block_max"] = {
        t: float(gumbel_r.ppf(1.0 - 1.0 / t, loc=loc, scale=scale)) for t in periods
    }

    # 2) GEV
    c, loc, scale = genextreme.fit(x)
    out["GEV_block_max"] = {
        t: float(genextreme.ppf(1.0 - 1.0 / t, c, loc=loc, scale=scale)) for t in periods
    }

    # 3) Weibull (benchmark; used in some wind-load extrapolation comparisons)
    # Force location=0 for interpretability/stability on positive maxima.
    k, loc, scale = weibull_min.fit(x, floc=0.0)
    out["Weibull_block_max"] = {
        t: float(weibull_min.ppf(1.0 - 1.0 / t, k, loc=loc, scale=scale)) for t in periods
    }

    # 4) Lognormal (benchmark model for positive skewed loads/winds)
    s, loc, scale = lognorm.fit(x, floc=0.0)
    out["Lognormal_block_max"] = {
        t: float(lognorm.ppf(1.0 - 1.0 / t, s, loc=loc, scale=scale)) for t in periods
    }

    return out


def alpha_sensitivity(
    ws10: pd.Series, ws100: pd.Series, hub_height_m: float, alphas: list[float]
) -> pd.DataFrame:
    rows = []
    for alpha in alphas:
        from10 = 1.10 * ws10 * (hub_height_m / 10.0) ** alpha
        from100 = 1.10 * ws100 * (hub_height_m / 100.0) ** alpha
        rows.append(
            {
                "alpha": alpha,
                "mean_vhub_from10": float(from10.mean()),
                "mean_vhub_from100": float(from100.mean()),
                "mean_abs_gap": float((from10 - from100).abs().mean()),
            }
        )
    return pd.DataFrame(rows)


def validation_metrics(ws10: pd.Series, ws100: pd.Series, alpha: float) -> dict[str, float]:
    ws100_from10 = ws10 * (100.0 / 10.0) ** alpha
    err = ws100_from10 - ws100
    return {
        "mean_actual_ws100": float(ws100.mean()),
        "mean_extrap_ws100_from10": float(ws100_from10.mean()),
        "bias": float(err.mean()),
        "mae": float(err.abs().mean()),
        "rmse": float(np.sqrt((err.pow(2)).mean())),
        "mape": float((err.abs() / ws100).mean() * 100.0),
    }


def save_plots(
    ts10: pd.Series,
    ts100: pd.Series,
    ws10: pd.Series,
    ws100: pd.Series,
    annual_max10: pd.Series,
    annual_max100: pd.Series,
    sensitivity_df: pd.DataFrame,
    mrl: pd.DataFrame,
    methods_df: pd.DataFrame,
    out_dir: Path,
) -> None:
    # Timeseries (monthly max for readability)
    monthly_max10 = ts10.resample("MS").max()
    monthly_max100 = ts100.resample("MS").max()
    plt.figure(figsize=(11, 4))
    plt.plot(monthly_max10.index, monthly_max10.values, lw=0.9, label="From 10 m")
    plt.plot(monthly_max100.index, monthly_max100.values, lw=0.9, label="From 100 m")
    plt.title("Monthly Max of Area-Mean Hub-Height 10-min Wind")
    plt.ylabel("Wind speed (m/s)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_timeseries_vhub_compare.png", dpi=180)
    plt.close()

    # Timeseries monthly means for a smoother comparison.
    monthly_mean10 = ts10.resample("MS").mean()
    monthly_mean100 = ts100.resample("MS").mean()
    plt.figure(figsize=(11, 4))
    plt.plot(monthly_mean10.index, monthly_mean10.values, lw=0.9, label="From 10 m")
    plt.plot(monthly_mean100.index, monthly_mean100.values, lw=0.9, label="From 100 m")
    plt.title("Monthly Mean of Area-Mean Hub-Height 10-min Wind")
    plt.ylabel("Wind speed (m/s)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_monthly_mean_vhub_compare.png", dpi=180)
    plt.close()

    monthly_mean_ws100 = ws100.resample("MS").mean()
    monthly_mean_ws100_from10 = (ws10 * (100.0 / 10.0) ** 0.11).resample("MS").mean()
    plt.figure(figsize=(11, 4))
    plt.plot(monthly_mean_ws100.index, monthly_mean_ws100.values, lw=0.9, label="Actual ERA5 100 m")
    plt.plot(monthly_mean_ws100_from10.index, monthly_mean_ws100_from10.values, lw=0.9, label="10 m extrapolated to 100 m")
    plt.title("Monthly Mean Validation: Actual 100 m vs 10 m Extrapolated to 100 m")
    plt.ylabel("Wind speed (m/s)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_monthly_mean_ws100_validation.png", dpi=180)
    plt.close()

    # Annual maxima
    plt.figure(figsize=(9, 4))
    plt.plot(annual_max10.index.year, annual_max10.values, marker="o", ms=3, lw=1.0, label="From 10 m")
    plt.plot(annual_max100.index.year, annual_max100.values, marker="o", ms=3, lw=1.0, label="From 100 m")
    plt.title("Annual Maxima of Area-Mean Hub-Height 10-min Wind")
    plt.ylabel("Annual maximum (m/s)")
    plt.xlabel("Year")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_annual_maxima_compare.png", dpi=180)
    plt.close()

    # Difference between the two extrapolation paths.
    monthly_gap = (ts10 - ts100).resample("MS").mean()
    plt.figure(figsize=(11, 4))
    plt.plot(monthly_gap.index, monthly_gap.values, lw=0.9)
    plt.axhline(0.0, color="black", lw=0.8, alpha=0.6)
    plt.title("Monthly Mean Gap: 10 m Based Minus 100 m Based Hub-Height Wind")
    plt.ylabel("Difference (m/s)")
    plt.xlabel("Time")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_extrapolation_gap.png", dpi=180)
    plt.close()

    # Simple summary comparison for meetings.
    bar_labels = ["Mean Vhub (10 m input)", "Mean Vhub (100 m input)"]
    bar_values = [float(ts10.mean()), float(ts100.mean())]
    plt.figure(figsize=(7, 4))
    bars = plt.bar(bar_labels, bar_values, width=0.55)
    plt.ylabel("Mean wind speed (m/s)")
    plt.title("Average Hub-Height 10-min Wind by Input Height")
    plt.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, bar_values):
        plt.text(bar.get_x() + bar.get_width() / 2, value + 0.05, f"{value:.2f}", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(out_dir / "fig_extrapolation_means_bar.png", dpi=180)
    plt.close()

    # Sensitivity of mean extrapolated wind to alpha.
    plt.figure(figsize=(8, 4.5))
    plt.plot(sensitivity_df["alpha"], sensitivity_df["mean_vhub_from10"], marker="o", label="From 10 m")
    plt.plot(sensitivity_df["alpha"], sensitivity_df["mean_vhub_from100"], marker="o", label="From 100 m")
    plt.title("Sensitivity of Mean Hub-Height Wind to Power-Law Exponent alpha")
    plt.xlabel("alpha")
    plt.ylabel("Mean hub-height 10-min wind (m/s)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_dir / "fig_alpha_sensitivity.png", dpi=180)
    plt.close()

    # Mean residual life plot
    if not mrl.empty:
        plt.figure(figsize=(8, 4))
        plt.plot(mrl["u"], mrl["mrl"], marker="o", ms=3, lw=1.0)
        plt.title("Mean Residual Life Plot (Threshold Diagnostic)")
        plt.xlabel("Threshold u (m/s)")
        plt.ylabel("Mean excess E[X-u | X>u] (m/s)")
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.savefig(out_dir / "fig_pot_mrl.png", dpi=180)
        plt.close()

    # Return-level comparison
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(methods_df))
    w = 0.35
    ax.bar(x - w / 2, methods_df["rl_50y"], width=w, label="50-year")
    ax.bar(x + w / 2, methods_df["rl_100y"], width=w, label="100-year")
    ax.set_xticks(x)
    ax.set_xticklabels(methods_df["method"], rotation=20, ha="right")
    ax.set_ylabel("Return level (m/s)")
    ax.set_title("Return-Level Estimates Across 5 Extreme-Value Methods")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "fig_return_levels.png", dpi=180)
    plt.close(fig)


def write_interpretation(
    out_dir: Path,
    ts10: pd.Series,
    ts100: pd.Series,
    annual_max: pd.Series,
    sensitivity_df: pd.DataFrame,
    validation: dict[str, float],
    threshold_q: float,
    threshold_u: float,
    n_peaks: int,
    methods_df: pd.DataFrame,
    gpd_shape: float,
    target_column: str,
) -> None:
    rows = methods_df.sort_values("rl_100y").reset_index(drop=True)
    method_lines = [f"- {r.method}: 50y={r.rl_50y:.2f} m/s, 100y={r.rl_100y:.2f} m/s" for r in rows.itertuples()]
    target_label = "from 10 m" if target_column == "vhub_10min_from10_mean" else "from 100 m"
    diff = ts10 - ts100
    diff_abs = diff.abs()

    md = [
        "# Extreme-Method Comparison: Interpretation Notes",
        "",
        "## What was analyzed",
        f"- Primary EVA variable: area-mean `{target_column}` ({target_label}).",
        "- Two hub-height series were constructed for comparison:",
        "  `vhub_10min_from10_mean` and `vhub_10min_from100_mean`.",
        f"- Coverage: {ts10.index.min().date()} to {ts10.index.max().date()} (~{(ts10.index.max()-ts10.index.min()).days/365.25:.1f} years).",
        f"- Annual maxima sample size: {len(annual_max)}.",
        "",
        "## Why compare 10 m and 100 m extrapolations?",
        "- The paper formulates the environmental wind variable at 10 m above mean sea level, so a 10 m based extrapolation is consistent with the paper setup.",
        "- ERA5 also provides 100 m wind, which is closer to hub height and may reduce sensitivity to the assumed power-law profile over a large vertical range.",
        "- Comparing both gives a direct sensitivity check on the shear-model assumption.",
        f"- Mean value from 10 m extrapolation: {ts10.mean():.2f} m/s.",
        f"- Mean value from 100 m extrapolation: {ts100.mean():.2f} m/s.",
        f"- Mean absolute gap between the two hub-height series: {diff_abs.mean():.2f} m/s.",
        "",
        "## Validation against actual ERA5 100 m wind",
        "- A useful internal check is to extrapolate the 10 m wind only up to 100 m and compare it with the actual ERA5 100 m wind.",
        f"- Mean actual ERA5 100 m wind: {validation['mean_actual_ws100']:.2f} m/s.",
        f"- Mean 10 m extrapolated to 100 m: {validation['mean_extrap_ws100_from10']:.2f} m/s.",
        f"- Bias of 10 m to 100 m extrapolation: {validation['bias']:.2f} m/s.",
        f"- MAE: {validation['mae']:.2f} m/s, RMSE: {validation['rmse']:.2f} m/s, MAPE: {validation['mape']:.2f}%.",
        "- If the 10 m based power-law extrapolation already overpredicts 100 m, that is evidence that the same setup may also overpredict 150 m relative to a 100 m based extrapolation.",
        "",
        "## Five methods tested",
        "- `Gumbel_block_max`: EVT block-maxima model used in your target paper.",
        "- `GEV_block_max`: general EVT block-maxima model (includes Gumbel as a special case).",
        "- `Weibull_block_max`: practical benchmark used in wind-load extrapolation comparisons.",
        "- `Lognormal_block_max`: practical benchmark for positive skewed responses.",
        "- `POT_GPD`: EVT peaks-over-threshold model on declustered exceedances.",
        "",
        "## Core formulas (for slide motivation)",
        "- 10 m extrapolation: `U_hub,10(1h) = U_10 * (z_hub/10)^alpha`.",
        "- 100 m extrapolation: `U_hub,100(1h) = U_100 * (z_hub/100)^alpha`.",
        "- 10-min conversion used in the paper setup: `V_hub(10min) = 1.10 * U_hub(1h)`.",
        "- Gumbel CDF (block maxima): `F(x) = exp(-exp(-(x-mu)/beta))`.",
        "- GEV CDF: `F(x) = exp(-(1+xi*(x-mu)/sigma)^(-1/xi))` with support `1+xi*(x-mu)/sigma > 0`.",
        "- POT/GPD exceedance model for `Y=X-u | X>u`: `P(Y<=y)=1-(1+xi*y/sigma_u)^(-1/xi)`.",
        "- Return level for period `T` years from POT with exceedance rate `lambda_u`:",
        "  `z_T = u + (sigma_u/xi)*((T*lambda_u)^xi - 1)` (or `u + sigma_u*log(T*lambda_u)` when `xi -> 0`).",
        "",
        "## POT choices",
        f"- Threshold quantile: q={threshold_q:.2f} (u={threshold_u:.2f} m/s).",
        f"- Declustered peaks used: {n_peaks}.",
        f"- Fitted GPD shape xi={gpd_shape:.3f}.",
        "",
        "## Return-level results (sorted by 100-year estimate)",
        *method_lines,
        "",
        "## How to explain these plots in slides",
        "- `fig_timeseries_vhub_compare.png`: shows whether the 10 m and 100 m based extrapolated series track each other closely through time.",
        "- `fig_monthly_mean_vhub_compare.png`: shows the smoother background-level comparison between 10 m and 100 m based extrapolations.",
        "- `fig_monthly_mean_ws100_validation.png`: checks whether the 10 m based power-law extrapolation reproduces the actual ERA5 100 m wind reasonably well.",
        "- `fig_annual_maxima_compare.png`: shows whether the block-maxima behavior changes materially depending on the source height.",
        "- `fig_extrapolation_gap.png`: shows how the difference between the two extrapolation paths changes over time.",
        "- `fig_extrapolation_means_bar.png`: gives the simplest overall comparison of the average extrapolated wind from 10 m versus 100 m.",
        "- `fig_alpha_sensitivity.png`: shows how strongly the extrapolated hub-height mean depends on the assumed shear exponent alpha.",
        "- `fig_pot_mrl.png`: threshold diagnostic; near-linear segment supports POT modeling in that region.",
        "- `fig_return_levels.png`: visual method spread (model-form uncertainty), useful for justifying conservative vs data-efficient choices.",
        "",
        "## Why the paper used Gumbel + ACER",
        "- Gumbel is simple and transparent for maxima-based short-term extrapolation.",
        "- The paper uses 10 m wind in its environmental description, which is conventional in offshore metocean modeling and tied to standard near-surface reference winds.",
        "- ACER uses more than one maximum per realization and handles dependence structure better than plain POT with ad hoc declustering.",
        "- In wind-turbine literature, ACER is often found to reduce uncertainty versus pure maxima fitting when limited simulations are available.",
        "- Their objective is short-term load extrapolation from finite OpenFAST realizations; ACER is designed exactly for that use case.",
        "",
        "## References to cite in your slides",
        "- Chai, W. et al. (2024). Short-term extreme value prediction for the structural responses of the IEA 15 MW offshore wind turbine under extreme environmental conditions. *Ocean Engineering*, 306, 118120. https://doi.org/10.1016/j.oceaneng.2024.118120",
        "- Gumbel, E.J. (1958). *Statistics of Extremes*. Columbia University Press.",
        "- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer. https://doi.org/10.1007/978-1-4471-3675-0",
        "- Pickands, J. (1975). Statistical inference using extreme order statistics. *Annals of Statistics*, 3(1), 119-131. https://doi.org/10.1214/AOS/1176343003",
        "- Balkema, A.A. & de Haan, L. (1974). Residual life time at great age. *Annals of Probability*, 2(5), 792-804. https://doi.org/10.1214/AOP/1176996548",
        "- Næss, A. & Gaidai, O. (2009). Estimation of extreme values from sampled time series. *Structural Safety*, 31(4), 325-334. https://doi.org/10.1016/j.strusafe.2008.06.021",
        "- Næss, A., Gaidai, O., & Karpa, O. (2013). Estimation of extreme values by the average conditional exceedance rate method. *Journal of Probability and Statistics*, 2013, 797014. https://doi.org/10.1155/2013/797014",
        "- Dimitrov, N. (2016). Comparative analysis of methods for modelling the short-term probability distribution of extreme wind turbine loads. *Wind Energy*, 19(4), 717-737. https://doi.org/10.1002/we.1861",
    ]
    (out_dir / "method_interpretation.md").write_text("\n".join(md), encoding="utf-8")


def write_extrapolation_notes(
    out_dir: Path, hub_height_m: float, baseline_alpha: float, sensitivity_df: pd.DataFrame, validation: dict[str, float]
) -> None:
    base_row = sensitivity_df.loc[np.isclose(sensitivity_df["alpha"], baseline_alpha)].iloc[0]
    md = [
        "# Extrapolation Formula Notes",
        "",
        "## Formula",
        "- `U_hub = U_ref * (z_hub / z_ref)^alpha`",
        "- `V_hub,10min = 1.10 * U_hub`",
        "",
        "## Meaning of each term",
        "- `U_ref`: the known wind speed at the reference height from ERA5.",
        "- `z_ref`: the height where that wind is measured, here either 10 m or 100 m.",
        f"- `z_hub`: the turbine hub height, here {hub_height_m:.0f} m.",
        "- `alpha`: the wind-shear exponent. It controls how quickly wind speed increases with height.",
        "- `1.10`: the paper's conversion from 1-hour mean hub-height wind to 10-minute mean hub-height wind.",
        "",
        "## Intuition",
        "- Wind is usually slower near the sea surface because of surface drag.",
        "- As height increases, that drag influence weakens, so the mean wind speed usually increases.",
        "- The exponent `alpha` controls the curvature of that increase.",
        "- Smaller `alpha` means weaker shear and less change with height.",
        "- Larger `alpha` means stronger shear and more amplification when extrapolating upward.",
        "",
        "## Why alpha = 0.11 in the paper?",
        "- The paper explicitly uses `alpha = 0.11` as its baseline assumption.",
        "- Their reason is consistency with the environmental model they use, which is defined using wind at 10 m above mean sea level.",
        "- In offshore settings, vertical shear is often weaker than over land because the sea surface is aerodynamically smoother, so a relatively low exponent is common.",
        "- For replication, using `alpha = 0.11` preserves consistency with the benchmark paper before introducing sensitivity tests.",
        "",
        "## How to judge whether 10 m or 100 m extrapolation is more accurate",
        "- Because ERA5 gives both 10 m and 100 m winds, the first internal validation is to extrapolate 10 m up to 100 m and compare that against the actual ERA5 100 m wind.",
        f"- For alpha={baseline_alpha:.2f}, the extrapolated 10 m to 100 m mean is {validation['mean_extrap_ws100_from10']:.2f} m/s, while the actual 100 m mean is {validation['mean_actual_ws100']:.2f} m/s.",
        f"- The bias is {validation['bias']:.2f} m/s and the MAE is {validation['mae']:.2f} m/s.",
        "- If the 10 m based extrapolation is already biased high at 100 m, that supports treating the 100 m based 150 m extrapolation as the more trustworthy of the two simple power-law estimates.",
        "",
        "## Why the 10 m based 150 m extrapolation is higher here",
        "- The 10 m to 150 m extrapolation spans a much larger height ratio than the 100 m to 150 m extrapolation.",
        "- With a positive alpha, the factor `(z_hub / z_ref)^alpha` grows as the vertical jump becomes larger.",
        "- If alpha is even slightly too large for the real offshore shear, the 10 m based extrapolation will amplify that mismatch more strongly than the 100 m based extrapolation.",
        "",
        "## What the sensitivity test shows here",
        f"- At alpha={baseline_alpha:.2f}, mean extrapolated `Vhub` from 10 m is {base_row['mean_vhub_from10']:.2f} m/s.",
        f"- At alpha={baseline_alpha:.2f}, mean extrapolated `Vhub` from 100 m is {base_row['mean_vhub_from100']:.2f} m/s.",
        "- The alpha-sensitivity plot shows that the 10 m based extrapolation is more sensitive to alpha than the 100 m based extrapolation, because it spans a larger vertical distance.",
        "- That is one strong reason to compare 10 m and 100 m based extrapolations explicitly.",
    ]
    (out_dir / "extrapolation_notes.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv, parse_dates=["time"]).sort_values("time")
    indexed = df.set_index("time")
    ts10 = indexed["vhub_10min_from10_mean"].dropna()
    ts100 = indexed["vhub_10min_from100_mean"].dropna()
    ts = indexed[args.target_column].dropna()
    ws10 = indexed["ws10_mean"].dropna()
    ws100 = indexed["ws100_mean"].dropna()
    alphas = [0.08, 0.10, 0.11, 0.14, 0.20]
    sensitivity_df = alpha_sensitivity(ws10, ws100, hub_height_m=150.0, alphas=alphas)
    sensitivity_df.to_csv(out_dir / "alpha_sensitivity.csv", index=False)
    validation = validation_metrics(ws10, ws100, alpha=0.11)

    annual_max = ts.resample("YS").max().dropna()
    annual_max10 = ts10.resample("YS").max().dropna()
    annual_max100 = ts100.resample("YS").max().dropna()
    periods = [50, 100]

    block_methods = fit_block_max_methods(annual_max, periods)
    threshold_u = float(ts.quantile(args.threshold_quantile))
    gpd_rl, n_peaks, gpd_params = rl_from_gpd(
        ts, threshold_u, periods=periods, min_gap_hours=args.min_gap_hours
    )

    rows = []
    for m, vals in block_methods.items():
        rows.append({"method": m, "rl_50y": vals[50], "rl_100y": vals[100]})
    rows.append({"method": "POT_GPD", "rl_50y": gpd_rl[50], "rl_100y": gpd_rl[100]})
    methods_df = pd.DataFrame(rows)
    methods_df.to_csv(out_dir / "method_comparison.csv", index=False)

    mrl = mrl_curve(ts)
    save_plots(ts10, ts100, ws10, ws100, annual_max10, annual_max100, sensitivity_df, mrl, methods_df, out_dir)
    write_interpretation(
        out_dir,
        ts10,
        ts100,
        annual_max,
        sensitivity_df,
        validation,
        args.threshold_quantile,
        threshold_u,
        n_peaks,
        methods_df,
        gpd_shape=gpd_params[0],
        target_column=args.target_column,
    )
    write_extrapolation_notes(
        out_dir,
        hub_height_m=150.0,
        baseline_alpha=0.11,
        sensitivity_df=sensitivity_df,
        validation=validation,
    )

    print(f"[OK] wrote {out_dir / 'method_comparison.csv'}")
    print(f"[OK] wrote {out_dir / 'method_interpretation.md'}")
    print(f"[OK] wrote {out_dir / 'extrapolation_notes.md'}")
    print(f"[OK] wrote plots in {out_dir}")


if __name__ == "__main__":
    main()
