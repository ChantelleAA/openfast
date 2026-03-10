# Today Demo Results

## Data Used
- Files processed: 306
- Time coverage: 1950-01-01 to 1975-06-30 (~25.5 years)
- Variables available in current files: wind only (`u10`, `v10`, `u100`, `v100`)
- Wave fields (`Hs`, `Tp`) are not present in these downloaded monthly files yet.

## Hub-Height Conversion (paper-consistent quick demo)
- Hub height: 150.0 m
- Power-law exponent: alpha=0.110
- Conversion used: `Uhub_1h = U10 * (Hhub/10)^alpha`
- 10-min scaling used: `Vhub_10min = 1.10 * Uhub_1h`

## Extreme Value Results (Area-Mean Vhub_10min)
- Annual maxima sample size (Gumbel): 26 years
- POT threshold quantile: 0.98
- POT threshold value: 24.223 m/s
- Declustered peaks used (GPD): 328

| Method | 50-year RL (m/s) | 100-year RL (m/s) |
|---|---:|---:|
| Gumbel (annual maxima) | 35.262 | 36.288 |
| POT/GPD | 32.946 | 33.213 |

## Notes for Meeting
- This is a quick demonstrator on the currently downloaded subset only.
- Next step is full-period completion and inclusion of wave variables for joint wind-wave contour work.