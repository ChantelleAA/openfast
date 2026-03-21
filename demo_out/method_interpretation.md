# Extreme-Method Comparison: Interpretation Notes

## What was analyzed
- Primary EVA variable: area-mean `vhub_10min_from10_mean` (from 10 m).
- Two hub-height series were constructed for comparison:
  `vhub_10min_from10_mean` and `vhub_10min_from100_mean`.
- Coverage: 1950-01-01 to 1981-03-31 (~31.2 years).
- Annual maxima sample size: 32.

## Why compare 10 m and 100 m extrapolations?
- The paper formulates the environmental wind variable at 10 m above mean sea level, so a 10 m based extrapolation is consistent with the paper setup.
- ERA5 also provides 100 m wind, which is closer to hub height and may reduce sensitivity to the assumed power-law profile over a large vertical range.
- Comparing both gives a direct sensitivity check on the shear-model assumption.
- Mean value from 10 m extrapolation: 12.37 m/s.
- Mean value from 100 m extrapolation: 11.55 m/s.
- Mean absolute gap between the two hub-height series: 0.96 m/s.

## Validation against actual ERA5 100 m wind
- A useful internal check is to extrapolate the 10 m wind only up to 100 m and compare it with the actual ERA5 100 m wind.
- Mean actual ERA5 100 m wind: 10.04 m/s.
- Mean 10 m extrapolated to 100 m: 10.75 m/s.
- Bias of 10 m to 100 m extrapolation: 0.71 m/s.
- MAE: 0.84 m/s, RMSE: 0.97 m/s, MAPE: 9.76%.
- If the 10 m based power-law extrapolation already overpredicts 100 m, that is evidence that the same setup may also overpredict 150 m relative to a 100 m based extrapolation.

## Five methods tested
- `Gumbel_block_max`: EVT block-maxima model used in your target paper.
- `GEV_block_max`: general EVT block-maxima model (includes Gumbel as a special case).
- `Weibull_block_max`: practical benchmark used in wind-load extrapolation comparisons.
- `Lognormal_block_max`: practical benchmark for positive skewed responses.
- `POT_GPD`: EVT peaks-over-threshold model on declustered exceedances.

## Core formulas (for slide motivation)
- 10 m extrapolation: `U_hub,10(1h) = U_10 * (z_hub/10)^alpha`.
- 100 m extrapolation: `U_hub,100(1h) = U_100 * (z_hub/100)^alpha`.
- 10-min conversion used in the paper setup: `V_hub(10min) = 1.10 * U_hub(1h)`.
- Gumbel CDF (block maxima): `F(x) = exp(-exp(-(x-mu)/beta))`.
- GEV CDF: `F(x) = exp(-(1+xi*(x-mu)/sigma)^(-1/xi))` with support `1+xi*(x-mu)/sigma > 0`.
- POT/GPD exceedance model for `Y=X-u | X>u`: `P(Y<=y)=1-(1+xi*y/sigma_u)^(-1/xi)`.
- Return level for period `T` years from POT with exceedance rate `lambda_u`:
  `z_T = u + (sigma_u/xi)*((T*lambda_u)^xi - 1)` (or `u + sigma_u*log(T*lambda_u)` when `xi -> 0`).

## POT choices
- Threshold quantile: q=0.95 (u=21.89 m/s).
- Declustered peaks used: 746.
- Fitted GPD shape xi=-0.327.

## Return-level results (sorted by 100-year estimate)
- Weibull_block_max: 50y=32.67 m/s, 100y=32.88 m/s
- GEV_block_max: 50y=32.74 m/s, 100y=32.90 m/s
- POT_GPD: 50y=32.91 m/s, 100y=33.16 m/s
- Lognormal_block_max: 50y=33.27 m/s, 100y=33.68 m/s
- Gumbel_block_max: 50y=35.30 m/s, 100y=36.31 m/s

## How to explain these plots in slides
- `fig_timeseries_vhub_compare.png`: shows whether the 10 m and 100 m based extrapolated series track each other closely through time.
- `fig_monthly_mean_vhub_compare.png`: shows the smoother background-level comparison between 10 m and 100 m based extrapolations.
- `fig_monthly_mean_ws100_validation.png`: checks whether the 10 m based power-law extrapolation reproduces the actual ERA5 100 m wind reasonably well.
- `fig_annual_maxima_compare.png`: shows whether the block-maxima behavior changes materially depending on the source height.
- `fig_extrapolation_gap.png`: shows how the difference between the two extrapolation paths changes over time.
- `fig_extrapolation_means_bar.png`: gives the simplest overall comparison of the average extrapolated wind from 10 m versus 100 m.
- `fig_alpha_sensitivity.png`: shows how strongly the extrapolated hub-height mean depends on the assumed shear exponent alpha.
- `fig_pot_mrl.png`: threshold diagnostic; near-linear segment supports POT modeling in that region.
- `fig_return_levels.png`: visual method spread (model-form uncertainty), useful for justifying conservative vs data-efficient choices.

## Why the paper used Gumbel + ACER
- Gumbel is simple and transparent for maxima-based short-term extrapolation.
- The paper uses 10 m wind in its environmental description, which is conventional in offshore metocean modeling and tied to standard near-surface reference winds.
- ACER uses more than one maximum per realization and handles dependence structure better than plain POT with ad hoc declustering.
- In wind-turbine literature, ACER is often found to reduce uncertainty versus pure maxima fitting when limited simulations are available.
- Their objective is short-term load extrapolation from finite OpenFAST realizations; ACER is designed exactly for that use case.

## References to cite in your slides
- Chai, W. et al. (2024). Short-term extreme value prediction for the structural responses of the IEA 15 MW offshore wind turbine under extreme environmental conditions. *Ocean Engineering*, 306, 118120. https://doi.org/10.1016/j.oceaneng.2024.118120
- Gumbel, E.J. (1958). *Statistics of Extremes*. Columbia University Press.
- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer. https://doi.org/10.1007/978-1-4471-3675-0
- Pickands, J. (1975). Statistical inference using extreme order statistics. *Annals of Statistics*, 3(1), 119-131. https://doi.org/10.1214/AOS/1176343003
- Balkema, A.A. & de Haan, L. (1974). Residual life time at great age. *Annals of Probability*, 2(5), 792-804. https://doi.org/10.1214/AOP/1176996548
- Næss, A. & Gaidai, O. (2009). Estimation of extreme values from sampled time series. *Structural Safety*, 31(4), 325-334. https://doi.org/10.1016/j.strusafe.2008.06.021
- Næss, A., Gaidai, O., & Karpa, O. (2013). Estimation of extreme values by the average conditional exceedance rate method. *Journal of Probability and Statistics*, 2013, 797014. https://doi.org/10.1155/2013/797014
- Dimitrov, N. (2016). Comparative analysis of methods for modelling the short-term probability distribution of extreme wind turbine loads. *Wind Energy*, 19(4), 717-737. https://doi.org/10.1002/we.1861