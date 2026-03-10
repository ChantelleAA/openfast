# Today Demo Results

## Data Used
- Files processed: 375
- Time coverage: 1950-01-01 to 1981-03-31 (~31.2 years)
- Variables available in current files: winds (`u10`, `v10`, `u100`, `v100`) and waves (`swh`, `pp1d`) after unpacking both inner NetCDF streams.

## Hub-Height Conversion (paper-consistent quick demo)
- Hub height: 150.0 m
- Power-law exponent: alpha=0.110
- 10 m based conversion: `Uhub_1h_from10 = U10 * (Hhub/10)^alpha`
- 100 m based conversion: `Uhub_1h_from100 = U100 * (Hhub/100)^alpha`
- 10-min scaling used: `Vhub_10min = 1.10 * Uhub_1h`

## Comparison of 10 m and 100 m based hub-height winds
- Mean absolute difference in `Vhub_10min`: 0.960 m/s
- Median absolute difference in `Vhub_10min`: 0.969 m/s
- Max absolute difference in `Vhub_10min`: 2.612 m/s
- Mean absolute percent difference in `Vhub_10min`: 8.66 %

## Extreme Value Results (Area-Mean Vhub_10min)
- Annual maxima sample size (Gumbel): 32 years
- POT threshold quantile: 0.95

| Series | Method | Threshold / sample | 50-year RL (m/s) | 100-year RL (m/s) |
|---|---|---:|---:|---:|
| From 10 m | Gumbel (annual maxima) | 32 years | 35.303 | 36.309 |
| From 10 m | POT/GPD | u=21.885, n=746 | 32.914 | 33.159 |
| From 100 m | Gumbel (annual maxima) | 32 years | 35.625 | 36.682 |
| From 100 m | POT/GPD | u=20.986, n=801 | 34.015 | 34.401 |

## Notes for Meeting
- This is a quick demonstrator on the currently downloaded subset only.
- The paper uses 10 m wind because its environmental model is formulated in terms of wind speed at 10 m above mean sea level.
- Comparing 10 m and 100 m based extrapolations is useful as a sensitivity check on the vertical-profile assumption.
- Next step is full-period completion and joint wind-wave contour work using the unpacked wave fields.