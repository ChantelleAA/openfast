# Meeting Slides Notes

## Slide 1: Objective and Current Scope

**Title**
- ERA5-based extreme wind workflow and paper replication plan

**Show**
- No figure needed

**Say**
- The replication target is the 2024 paper on short-term extreme structural responses for the IEA 15 MW turbine.
- My immediate goal was to build a defensible preliminary ERA5 workflow using the data already downloaded, so I could test hub-height extrapolation and several extreme-value methods on real data.
- This is not yet the full wind-wave contour replication, but it is a working first step toward it.

**Key points**
- Current demo coverage: 1950-01-01 to 1981-03-31
- Current demo uses ERA5 winds and unpacked wave fields, but the analysis shown here is still focused on wind
- The full replication still requires the joint wind-wave environmental model and the OpenFAST response stage

---

## Slide 2: Extrapolation Formula and Why the Paper Uses 10 m

**Title**
- Hub-height wind extrapolation: formula, intuition, and baseline assumptions

**Show**
- Formula only:
- `U_hub = U_ref * (z_hub / z_ref)^alpha`
- `V_hub,10min = 1.10 * U_hub`

**Say**
- The paper defines the environmental wind variable at 10 m above mean sea level, so using 10 m as the reference height is the paper-consistent baseline.
- In the formula, `U_ref` is the known wind speed at the reference height, `z_ref` is either 10 m or 100 m, `z_hub` is 150 m, and `alpha` is the wind-shear exponent.
- Physically, wind is slower near the sea surface because of drag, and it generally increases with height, so the formula is trying to represent that vertical shear in a simple way.
- The paper uses `alpha = 0.11`, which is a relatively low offshore-type shear assumption and preserves consistency with their environmental setup.

**Interpretation**
- A larger `alpha` means stronger shear and therefore more amplification when extrapolating upward.
- Because 10 m is much farther from 150 m than 100 m is, the 10 m based extrapolation is much more sensitive to the choice of `alpha`.

---

## Slide 3: 10 m vs 100 m Extrapolation and Internal Validation

**Title**
- Comparing 10 m and 100 m extrapolations, and validating against actual 100 m ERA5 wind

**Show**
- [fig_monthly_mean_vhub_compare.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_monthly_mean_vhub_compare.png)
- [fig_monthly_mean_ws100_validation.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_monthly_mean_ws100_validation.png)
- [fig_extrapolation_means_bar.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_extrapolation_means_bar.png)

**Say**
- I computed the 150 m hub-height wind in two ways: from the ERA5 10 m wind and from the ERA5 100 m wind.
- The monthly-mean comparison shows that the 10 m based extrapolation is systematically higher than the 100 m based extrapolation.
- To check which one is more believable, I used the actual ERA5 100 m wind as an internal validation target.
- I extrapolated the 10 m wind only up to 100 m and compared that against the actual 100 m ERA5 wind.
- With `alpha = 0.11`, the extrapolated 10 m to 100 m mean is `10.75 m/s`, while the actual 100 m mean is `10.04 m/s`, so the 10 m based extrapolation is biased high.

**Key numbers**
- Mean 150 m wind from 10 m input: `12.37 m/s`
- Mean 150 m wind from 100 m input: `11.55 m/s`
- Mean absolute difference between the two 150 m series: `0.96 m/s`
- 10 m to 100 m validation bias: `+0.71 m/s`
- 10 m to 100 m validation MAE: `0.84 m/s`

**Interpretation**
- Since the 10 m based extrapolation already overpredicts the actual 100 m wind, it is plausible that it also overpredicts 150 m.
- That makes the 100 m based 150 m extrapolation the more trustworthy of the two simple power-law estimates, while the 10 m based extrapolation remains the paper-consistent baseline.

---

## Slide 4: Sensitivity to alpha

**Title**
- Sensitivity of hub-height wind to the power-law exponent

**Show**
- [fig_alpha_sensitivity.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_alpha_sensitivity.png)

**Say**
- I varied `alpha` to see how strongly the extrapolated hub-height wind depends on the assumed shear.
- The key result is that the 10 m based extrapolation is much more sensitive to `alpha` than the 100 m based extrapolation.
- That is expected, because the 10 m method spans a much larger vertical jump.
- So if `alpha` is even slightly misspecified, the 10 m based 150 m estimate will move much more than the 100 m based estimate.

**Useful examples**
- At `alpha = 0.11`, mean `Vhub` from 10 m is `12.37 m/s`
- At `alpha = 0.11`, mean `Vhub` from 100 m is `11.55 m/s`
- As `alpha` increases, the 10 m based curve rises much more quickly than the 100 m based curve

**Interpretation**
- This supports a sensible presentation strategy:
- use the 10 m based result as the strict paper-consistent baseline
- use the 100 m based result as a sensitivity check that is likely less exposed to shear-model error

---

## Slide 5: Extreme-Value Methods and What They Tell Us

**Title**
- Comparing five extreme-value methods to quantify model-form uncertainty

**Show**
- [fig_pot_mrl.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_pot_mrl.png)
- [fig_return_levels.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_return_levels.png)
- [method_comparison.csv](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/method_comparison.csv)

**Say**
- I tested five methods: Gumbel, GEV, Weibull, lognormal, and POT/GPD.
- The reason for trying several methods is to quantify model-form uncertainty rather than rely on a single extrapolation model.
- The mean residual life plot is the threshold diagnostic for POT, and it is there to justify the threshold choice.
- The return-level comparison shows that Gumbel is the most conservative on this subset, while the other methods cluster closer together.

**Key numbers for the 10 m based 150 m series**
- Gumbel 100-year return level: `36.31 m/s`
- GEV 100-year return level: `32.90 m/s`
- Weibull 100-year return level: `32.88 m/s`
- Lognormal 100-year return level: `33.68 m/s`
- POT/GPD 100-year return level: `33.16 m/s`

**Interpretation**
- The method choice matters materially.
- Gumbel is simple and conservative, which helps explain why the paper uses it as one of its short-term extrapolation methods.

---

## Slide 6: Why the Paper Uses Gumbel and ACER, and What Comes Next

**Title**
- Linking the ERA5 preprocessing work to the full paper replication

**Show**
- No figure needed

**Say**
- The paper’s final objective is short-term structural response extrapolation from finite OpenFAST realizations, not just wind extrapolation.
- That is why Gumbel and ACER are a sensible pair in that context.
- Gumbel is a transparent maxima-based extrapolation.
- ACER is designed for sampled dependent time series and uses peaks more efficiently than relying on one maximum per realization.
- So the present ERA5 work is the environmental-input stage that will later feed the contour selection and structural-response stage.

**Next steps**
- Complete the full ERA5 time period
- Build the joint wind-wave environmental model in terms of `Uw`, `Hs`, and `Tp`
- Reproduce the paper’s environmental contour and condition-selection logic
- Then apply Gumbel and ACER to the actual OpenFAST response channels

**Supervisor questions**
- Should I keep the first full replication strictly in the northern North Sea before extending to other regions?
- Do you want the 10 m paper-consistent baseline only first, or should I carry both 10 m and 100 m extrapolation paths as a formal sensitivity analysis from the start?

---

## Backup Notes

**Main formulas**
- `U_hub = U_ref * (z_hub / z_ref)^alpha`
- `V_hub,10min = 1.10 * U_hub`
- Gumbel CDF: `F(x) = exp(-exp(-(x-mu)/beta))`
- GEV CDF: `F(x) = exp(-(1 + xi * (x-mu) / sigma)^(-1/xi))`
- GPD exceedance model: `P(Y <= y) = 1 - (1 + xi*y/sigma_u)^(-1/xi)`

**One-line method rationale**
- Gumbel: simple block-maxima benchmark and used in the paper
- GEV: more flexible block-maxima EVT model
- POT/GPD: uses more tail data than annual maxima
- Weibull: practical engineering benchmark for positive wind/load variables
- Lognormal: benchmark for positive skewed variables
- ACER: designed for extreme estimation from sampled dependent response time series
