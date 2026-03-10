# Meeting Slides Notes

## Slide 1: Current Status and Objective

**Title**
- Current ERA5-based extreme wind workflow and paper replication path

**Show**
- No figure needed, or a simple project workflow diagram if you make one manually

**Say**
- I started from the replication target in Chai et al. (2024), where short-term extreme structural responses for the IEA 15 MW turbine are estimated under extreme environmental conditions.
- In parallel, I started building the climate-data side using ERA5 so I can later replace the stationary environmental conditions in the paper with time-evolving ones.
- At the moment I have a working preliminary pipeline on the subset of data already downloaded, which lets me demonstrate hub-height wind extrapolation and several extreme-value methods on real data.

**Key points**
- Downloaded coverage currently used in the demo: 1950-01-01 to 1975-06-30
- Current files used in the demo contain wind variables only: `u10`, `v10`, `u100`, `v100`
- So this is a wind-only preliminary analysis, not yet the full wind-wave contour replication

---

## Slide 2: Why extrapolate to 150 m?

**Title**
- Hub-height conversion motivated by the paper setup

**Show**
- If possible, one simple text box with the formula:
- `U_hub(1h) = U_10 * (z_hub / 10)^alpha`
- `V_hub(10min) = 1.10 * U_hub(1h)`

**Say**
- The paper works with the IEA 15 MW turbine at a 150 m hub height, so to stay consistent with the replication target I converted ERA5 10 m winds to 150 m.
- The paper explicitly uses the power-law wind profile with exponent `alpha = 0.11`.
- After that, the paper converts from a 1-hour mean hub-height wind to a 10-minute mean by applying a 10% increase.
- I used the same assumptions here because the point of this first step is not to invent a new atmospheric model, but to stay aligned with the exact assumptions of the benchmark paper.

**Interpretation**
- This gives a paper-consistent hub-height wind variable that can later feed both environmental contour work and turbine load studies.
- It also isolates one assumption clearly, so later I can test sensitivity to `alpha` instead of mixing assumptions from the start.

**References**
- Chai et al. (2024)
- IEC-style power-law shear assumption as cited in the paper

---

## Slide 3: What does the time series tell us?

**Title**
- Time-series structure of the hub-height wind extremes

**Show**
- [fig_timeseries_vhub.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_timeseries_vhub.png)
- [fig_annual_maxima.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_annual_maxima.png)

**Say**
- The first figure shows the monthly maxima of the area-mean hub-height 10-minute equivalent wind speed.
- Its purpose is diagnostic: before fitting any extreme-value model, I need to see whether the data actually contain repeated high-end excursions and whether there are obvious discontinuities.
- The second figure extracts annual maxima, which is the standard starting point for block-maxima methods such as Gumbel and GEV.
- On this current subset, the annual maxima are reasonably stable in magnitude and do not show an obvious dramatic shift, although this is only about 25.5 years of data and not yet the full period Andrew asked for.

**Interpretation**
- These plots justify that block-maxima modeling is feasible.
- They also show why longer coverage matters: with only 26 annual maxima, the uncertainty in 50-year and 100-year return levels is still substantial.

---

## Slide 4: Why test multiple extreme-value methods?

**Title**
- Comparing five extreme-value models to quantify model-form uncertainty

**Show**
- [fig_pot_mrl.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_pot_mrl.png)
- [fig_return_levels.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_return_levels.png)

**Say**
- I tested five methods because one of the main technical questions is not just “what is the return level,” but “how sensitive is the answer to the method used.”
- The methods I tested are Gumbel, GEV, Weibull, lognormal, and POT with a generalized Pareto tail.
- Gumbel and GEV are classical EVT block-maxima models.
- POT/GPD is a threshold-based EVT method that can use more extreme observations than annual maxima alone.
- Weibull and lognormal are useful benchmarks because they are often used as practical engineering fits for positive skewed wind or load variables, even if they are not the purest EVT choice.

**How to motivate the threshold plot**
- The mean residual life plot is a standard diagnostic for POT.
- If the mean excess above threshold behaves approximately linearly over a threshold range, that supports the use of a GPD tail model in that region.
- So the plot is there to justify threshold selection rather than to present a final result by itself.

**References**
- Coles (2001)
- Pickands (1975)
- Balkema and de Haan (1974)
- Dimitrov (2016)

---

## Slide 5: What did the methods give?

**Title**
- Return-level estimates from five methods

**Show**
- [method_comparison.csv](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/method_comparison.csv)
- [fig_return_levels.png](/home/chantelle/Desktop/PhD Project/code/openfast/demo_out/fig_return_levels.png)

**Say**
- On the current subset, the 100-year return-level estimates are:
- Gumbel: about `36.29 m/s`
- GEV: about `32.98 m/s`
- Weibull: about `32.97 m/s`
- Lognormal: about `33.77 m/s`
- POT/GPD: about `33.16 m/s`
- The main takeaway is that Gumbel is the most conservative among the models I tried on this subset.
- The other methods cluster more closely around roughly `33 m/s`.

**Interpretation**
- This spread is useful because it quantifies model-form uncertainty.
- It also helps explain why the paper uses Gumbel but then also compares it against ACER.
- Gumbel is simple, transparent, and conservative, but it uses only block maxima.
- In contrast, ACER is designed for short-term response extrapolation from simulated time series and makes fuller use of the peaks in each realization.

**How to phrase the limitation**
- These are not yet final thesis values.
- They are preliminary wind-only estimates from an incomplete subset and are intended to demonstrate method setup and reasoning.

---

## Slide 6: Why did the paper choose Gumbel and ACER, and what do I do next?

**Title**
- Linking the preliminary ERA5 analysis to the paper replication

**Show**
- No figure needed, or a short bullets slide

**Say**
- The paper’s modeling problem is short-term structural response extrapolation from finite OpenFAST realizations.
- That is why Gumbel and ACER are a sensible pair in that context.
- Gumbel gives a simple maxima-based extrapolation.
- ACER is more data-efficient because it uses peaks rather than only one maximum per simulation and is specifically designed for sampled dependent time series.
- So the paper’s method choice is motivated by the structure of the simulation outputs, not just by convention.

**Next steps**
- Complete the full ERA5 download period
- Retrieve or regenerate the wave variables needed for `Uw`, `Hs`, `Tp`
- Build the joint environmental model and 100-year contours
- Reproduce the paper’s environmental condition selection logic
- Then compare Gumbel and ACER on the actual OpenFAST response channels, not only on wind speed

**Supervisor questions to ask**
- Should the first full replication stay strictly in the northern North Sea before extending to Ireland or the Atlantic?
- Do you want the first pass to preserve the paper assumptions exactly, then add sensitivity tests, or should the sensitivity tests be included immediately?

---

## Backup Notes

**Formulas**
- `U_hub(1h) = U_10 * (z_hub / 10)^alpha`
- `V_hub(10min) = 1.10 * U_hub(1h)`
- Gumbel CDF: `F(x) = exp(-exp(-(x-mu)/beta))`
- GEV CDF: `F(x) = exp(-(1 + xi * (x-mu) / sigma)^(-1/xi))`
- GPD exceedance model: `P(Y <= y) = 1 - (1 + xi*y/sigma_u)^(-1/xi)`

**Method rationale in one line each**
- Gumbel: simple block-maxima benchmark and used in the paper
- GEV: more flexible block-maxima EVT model
- POT/GPD: uses more tail data than annual maxima
- Weibull: common engineering benchmark for positive wind/load variables
- Lognormal: benchmark for positive skewed variables
- ACER: designed for extreme estimation from sampled dependent time series, especially useful for response peaks from finite simulations

