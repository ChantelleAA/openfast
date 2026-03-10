Today Before Meeting (March 9, 2026)

1) Demonstrate hub-height extrapolation and simple EVA with existing data

Script:
- `quick_demo_extremes.py`

Run:
- `python quick_demo_extremes.py`

Outputs:
- `demo_out/demo_timeseries.csv`
- `demo_out/today_demo_summary.md`

Current demo result snapshot (using currently downloaded subset only):
- Files processed: 306
- Coverage: 1950-01-01 to 1975-06-30 (~25.5 years)
- Method 1 (Gumbel annual maxima) return levels:
  - 50-year: 35.262 m/s
  - 100-year: 36.288 m/s
- Method 2 (POT/GPD) return levels:
  - 50-year: 32.912 m/s
  - 100-year: 33.165 m/s

2) Optional sensitivity run to show method stability

Run:
- `python quick_demo_extremes.py --output-dir demo_out_q98 --threshold-quantile 0.98`

Observation:
- POT/GPD return levels are similar to q=0.95 run, showing quick-method stability on current subset.

3) Explicit caveat to mention in meeting

- Current monthly files contain wind variables (`u10`, `v10`, `u100`, `v100`) but not wave variables (`Hs`, `Tp`), so this is a wind-only preliminary demo.

4) Deep-understanding package (formulas + 5 EVA methods + plot interpretation)

Script:
- `compare_extreme_methods.py`

Run:
- `python compare_extreme_methods.py`

Outputs:
- `demo_out/method_comparison.csv` (5-method RL table)
- `demo_out/fig_timeseries_vhub.png`
- `demo_out/fig_annual_maxima.png`
- `demo_out/fig_pot_mrl.png`
- `demo_out/fig_return_levels.png`
- `demo_out/method_interpretation.md` (formulas, motivation, citations, speaking notes)

Full Plan of Action

Phase 0: Lock Scope (1–2 days)

Confirm final primary area with supervisors.
Default to northern North Sea now (per Andrew), but keep area config externalized.
Confirm final hub height value used for your 15 MW model (paper uses 150 m).
Phase 1: Data Completion and QC (2–4 days)

Complete ERA5 monthly downloads for full period (your archive currently stops in 1975-03).
Variables: 10 m and 100 m wind components, significant wave height, peak period.
Build automated completeness report: missing year-month files, zero-byte files, hash/meta mismatches.
Build basic data QC report: min/max, missingness, coordinate consistency, timestamp continuity.
Phase 2: Derived Environmental Time Series (3–5 days)

Compute wind speed and direction at 10 m and 100 m from u/v.
Implement hub-height conversion module:
baseline paper-consistent method (alpha=0.11, 10 m to 150 m)
optional dynamic shear method (10 m + 100 m pair) as sensitivity.
Convert 1-h mean to 10-min mean using paper’s +10% factor (for strict replication).
Produce clean hourly/aggregated datasets for Uw, Hs, Tp, Uhub, Vhub.
Phase 3: Environmental Statistics and Contours (5–8 days)

Fit the paper-style joint model f(Uw) f(Hs|Uw) f(Tp|Hs,Uw).
Generate 100-year contours using IFORM + Rosenblatt transform.
Recreate EC selection logic (EC1–EC5-style points) for the baseline replication period.
Validate by comparing contour shapes/ranges and EC magnitudes against paper-level behavior.
Phase 4: Extreme Response Reproduction (7–12 days, depends on simulation runtime)

Set OpenFAST batch runs for selected ECs.
Match paper Monte Carlo structure where feasible:
50 realizations per EC
4200 s runtime
discard first 600 s
analyze 3600 s
Extract response channels:
mooring tensions (lines 1–3)
TwrBsFyt
TwrBsMxt
Reproduce summary stats and PSD checks for representative ECs.
Phase 5: ACER and Gumbel Reproduction (4–7 days)

Implement Gumbel extreme estimation on maxima (λ=0.01).
Implement ACER estimation with convergence check and ACER2 selection.
Compute uncertainty/CI outputs in paper-style tables.
Compare ACER vs Gumbel conservatism and consistency.
Phase 6: Climate-Change Extension (core PhD contribution) (7–14 days)

Split ERA5 into moving windows (example: 30-year windows stepped yearly, or decade blocks).
Refit environmental model per window.
Track nonstationary return levels (50-year and 100-year) over time.
Regenerate EC-like design conditions over time.
Re-run reduced OpenFAST campaign on selected time slices (early/mid/recent) to show response shifts.
Quantify trend and uncertainty in environmental extremes and structural extremes.
Phase 7: Packaging and Reporting (3–5 days)

Create reproducible scripts and config-driven pipeline.
Produce final figures/tables:
contour evolution
50y/100y return-level trajectories
ACER vs Gumbel comparison
response change across decades
Write methods/assumptions/limitations clearly for supervisor review.
Repository Implementation Structure

download_era5.py (existing; add resume/completeness helpers).
check_data_inventory.py (coverage/QC report).
build_env_timeseries.py (derive Uw, Hs, Tp, hub conversions).
fit_joint_model.py (distribution fitting).
build_contours.py (IFORM/Rosenblatt contours).
select_ec_cases.py (EC point selection).
run_openfast_batch.py (batch runs).
extract_openfast_stats.py (means/std/max/PSD).
fit_extremes_gumbel.py and fit_extremes_acer.py.
analyze_nonstationary_extremes.py (windowed trends).
configs/*.yaml for area, years, hub height, return periods, run settings.
Success Criteria

You can reproduce paper-like baseline behavior (EC ordering, ACER vs Gumbel relationship, response trends).
You can produce 50y/100y return-level changes over the ERA5 history.
You can show how those changing extremes alter key OpenFAST response extremes.
Entire workflow is rerunnable for a new area by changing config only.
Critical Decisions to Resolve Early

Final study area for thesis primary results (North Sea only vs additional Atlantic/Ireland).
Exact turbine setup/hub height for your OpenFAST model.
Windowing strategy for “changing over time” analysis.
Whether strict paper assumptions (alpha=0.11, +10%) are mandatory baseline before sensitivity tests.
Immediate Next Steps (this week)

Finish ERA5 archive to full target period and generate completeness/QC report.
Build derived environmental dataset (Uw, Hs, Tp, Uhub, Vhub) and verify distributions.
Implement baseline contour + EC selection script and compare against paper EC scale.
Prepare one pilot EC OpenFAST batch to validate end-to-end extraction and extreme fitting.
