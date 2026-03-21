# Extrapolation Formula Notes

## Formula
- `U_hub = U_ref * (z_hub / z_ref)^alpha`
- `V_hub,10min = 1.10 * U_hub`

## Meaning of each term
- `U_ref`: the known wind speed at the reference height from ERA5.
- `z_ref`: the height where that wind is measured, here either 10 m or 100 m.
- `z_hub`: the turbine hub height, here 150 m.
- `alpha`: the wind-shear exponent. It controls how quickly wind speed increases with height.
- `1.10`: the paper's conversion from 1-hour mean hub-height wind to 10-minute mean hub-height wind.

## Intuition
- Wind is usually slower near the sea surface because of surface drag.
- As height increases, that drag influence weakens, so the mean wind speed usually increases.
- The exponent `alpha` controls the curvature of that increase.
- Smaller `alpha` means weaker shear and less change with height.
- Larger `alpha` means stronger shear and more amplification when extrapolating upward.

## Why alpha = 0.11 in the paper?
- The paper explicitly uses `alpha = 0.11` as its baseline assumption.
- Their reason is consistency with the environmental model they use, which is defined using wind at 10 m above mean sea level.
- In offshore settings, vertical shear is often weaker than over land because the sea surface is aerodynamically smoother, so a relatively low exponent is common.
- For replication, using `alpha = 0.11` preserves consistency with the benchmark paper before introducing sensitivity tests.

## How to judge whether 10 m or 100 m extrapolation is more accurate
- Because ERA5 gives both 10 m and 100 m winds, the first internal validation is to extrapolate 10 m up to 100 m and compare that against the actual ERA5 100 m wind.
- For alpha=0.11, the extrapolated 10 m to 100 m mean is 10.75 m/s, while the actual 100 m mean is 10.04 m/s.
- The bias is 0.71 m/s and the MAE is 0.84 m/s.
- If the 10 m based extrapolation is already biased high at 100 m, that supports treating the 100 m based 150 m extrapolation as the more trustworthy of the two simple power-law estimates.

## Why the 10 m based 150 m extrapolation is higher here
- The 10 m to 150 m extrapolation spans a much larger height ratio than the 100 m to 150 m extrapolation.
- With a positive alpha, the factor `(z_hub / z_ref)^alpha` grows as the vertical jump becomes larger.
- If alpha is even slightly too large for the real offshore shear, the 10 m based extrapolation will amplify that mismatch more strongly than the 100 m based extrapolation.

## What the sensitivity test shows here
- At alpha=0.11, mean extrapolated `Vhub` from 10 m is 12.37 m/s.
- At alpha=0.11, mean extrapolated `Vhub` from 100 m is 11.55 m/s.
- The alpha-sensitivity plot shows that the 10 m based extrapolation is more sensitive to alpha than the 100 m based extrapolation, because it spans a larger vertical distance.
- That is one strong reason to compare 10 m and 100 m based extrapolations explicitly.