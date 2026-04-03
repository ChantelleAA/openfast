# Complete Implementation Guide: Joint Distribution of W, Hs, Tp from ERA5

---

## Before You Write a Single Line of Code

**What you are trying to do, in plain English:**

You have 65 years of hourly weather data. At every hour, three things were recorded simultaneously: how fast the wind was blowing, how high the waves were, and what period (rhythm) those waves had. These three things are physically connected — strong wind tends to produce high, long-period waves — so you cannot treat them independently.

Your goal is to answer the question: *what combinations of wind speed, wave height, and wave period are so extreme that they would only be exceeded, on average, once every 100 years?* The answer is not a single point — it is a surface in 3D space. Every point on that surface is equally extreme, just in different ways (e.g. very high wind with moderate waves, versus moderate wind with very high waves).

This is exactly what Johannessen et al. (2002) did with measured data from 1973–1999. You are doing it with ERA5 reanalysis data from 1960–2025.

---

## The Mathematical Strategy (Read This Before Anything Else)

The key insight from Johannessen (equation 1 in your paper fragment) is that a joint distribution of three variables can always be written as a chain of simpler distributions:

$$f(W, H_{m0}, T_p) = f_W(w) \cdot f_{H_{m0}|W}(h|w) \cdot f_{T_p|H_{m0},W}(t|h,w)$$

In plain English: the probability of seeing a particular combination of (W, Hs, Tp) simultaneously equals:
- The probability of that wind speed occurring **times**
- The probability of that wave height occurring *given that wind speed* **times**
- The probability of that wave period occurring *given both that wind speed and wave height*

This is not an assumption — it is mathematically exact (it is just the chain rule of probability). The assumptions come in when you decide *what shape* each of those three distributions has. Johannessen chose Weibull distributions for the first two and a Lognormal for the third. The MDPI 2023 paper makes the same choices and explains them in more detail.

---

## Your Python Environment

Set this up first. Every step below assumes these libraries are available.

```python
# Install these if you haven't already
# pip install numpy scipy xarray netCDF4 matplotlib pandas

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
from scipy.special import gamma
```

**Why each library:**
- `numpy` — all numerical operations
- `pandas` — working with timeseries data in a table
- `xarray` — reading and handling NetCDF files (this is the standard tool for gridded climate data)
- `matplotlib` — plotting everything so you can see what is happening
- `scipy.stats` — fitting statistical distributions
- `scipy.optimize.curve_fit` — fitting smooth curves to your parameter estimates
- `scipy.special.gamma` — needed for the Weibull method of moments calculation

---

## STEP 1 — Load and Prepare Your ERA5 Data

### What you are doing and why

Your ERA5 data is in NetCDF format, which is a structured binary file containing gridded data across time and space. You need to open it, find the variables you need, select your target location, and convert everything into a clean flat table of (timestamp, W, Hs, Tp).

ERA5 stores wind as two separate components: u10 (east-west wind) and v10 (north-south wind). You need to compute the total wind speed magnitude from these. Significant wave height is stored as `swh`. Peak wave period is stored as `pp1d`.

### Code

```python
# Open your ERA5 NetCDF file(s)
# If you have multiple files (e.g. one per year), use xr.open_mfdataset
ds = xr.open_dataset('your_era5_file.nc')

# Look at what is inside your file
print(ds)

# You will see variable names, dimensions, coordinates
# Common ERA5 variable names:
#   u10 = 10m eastward wind (m/s)
#   v10 = 10m northward wind (m/s)
#   swh = significant height of combined wind waves and swell (m)
#   pp1d = peak wave period (s)
# These names may vary depending on how you downloaded the data
# If names differ, check with: print(list(ds.data_vars))

# Select your target location
# Replace with your actual lat/lon
target_lat = 60.0
target_lon = 2.0

# ERA5 is a grid - select the nearest grid point to your location
ds_point = ds.sel(latitude=target_lat, longitude=target_lon, method='nearest')

# Compute wind speed magnitude from components
# W = sqrt(u10^2 + v10^2) - this is basic Pythagoras
u10 = ds_point['u10'].values  # eastward component
v10 = ds_point['v10'].values  # northward component
W = np.sqrt(u10**2 + v10**2)  # total wind speed magnitude

# Extract wave height and period
Hs = ds_point['swh'].values
Tp = ds_point['pp1d'].values

# Get timestamps
time = ds_point['time'].values

# Build a clean pandas DataFrame
df = pd.DataFrame({
    'time': time,
    'W': W,
    'Hs': Hs,
    'Tp': Tp
})

# Set time as the index
df = df.set_index('time')

print(df.head(10))
print(f"\nTotal records: {len(df)}")
print(f"\nDate range: {df.index[0]} to {df.index[-1]}")
```

### Cleaning the data

```python
# Check for missing values (NaN)
print("\nMissing values per variable:")
print(df.isna().sum())

# Remove any rows where any variable is missing
df_clean = df.dropna()
print(f"\nRecords after removing NaN: {len(df_clean)}")

# Check for physically impossible values
# Wind speed should be positive
# Wave height should be positive
# Wave period should be positive and physically reasonable (typically 1-30s)
print("\nBasic statistics:")
print(df_clean.describe())

# Remove records where any variable is zero or negative
df_clean = df_clean[(df_clean['W'] > 0) & 
                    (df_clean['Hs'] > 0) & 
                    (df_clean['Tp'] > 0)]

print(f"\nFinal clean records: {len(df_clean)}")
# For 65 years of hourly data you expect roughly 65 * 8766 ≈ 569,790 records
```

### Quick visual check

```python
fig, axes = plt.subplots(3, 1, figsize=(14, 8))

axes[0].plot(df_clean.index, df_clean['W'], linewidth=0.3, alpha=0.6)
axes[0].set_ylabel('Wind Speed W (m/s)')
axes[0].set_title('ERA5 Timeseries at Target Location')

axes[1].plot(df_clean.index, df_clean['Hs'], linewidth=0.3, alpha=0.6, color='steelblue')
axes[1].set_ylabel('Significant Wave Height Hs (m)')

axes[2].plot(df_clean.index, df_clean['Tp'], linewidth=0.3, alpha=0.6, color='darkorange')
axes[2].set_ylabel('Peak Period Tp (s)')

plt.tight_layout()
plt.savefig('timeseries_check.png', dpi=150)
plt.show()
```

**What you are looking for:** No sudden jumps or gaps that would suggest data problems. Seasonal cycles should be visible — winter should show higher values.

---

## STEP 2 — Fit the Marginal Distribution of Wind Speed W

### What you are doing and why

This corresponds directly to the section **"MARGINAL DISTRIBUTION FOR WIND, W"** in the Johannessen paper. Johannessen states:

> *"We will assume that the marginal distribution of the 1-h mean wind speed at 10m can be described by the 2-parameter Weibull distribution"*

The 2-parameter Weibull CDF is:

$$F(W) = 1 - \exp\left[-\left(\frac{W}{\beta}\right)^\alpha\right]$$

where α is the **shape parameter** (controls how skewed the distribution is) and β is the **scale parameter** (controls the typical magnitude). Johannessen found α = 1.708 and β = 8.426 for the North Sea. Your values will be different because your location is different.

**Why Weibull?** Wind speeds are always positive, tend to be right-skewed (most hours have moderate wind, rare hours have extreme wind), and the Weibull distribution has been used for wind speeds in offshore engineering for decades. It fits well empirically.

**Why method of moments?** Johannessen uses method of moments to estimate the parameters. This means you compute the mean and variance of your observed data and solve for the distribution parameters that would produce that same mean and variance. It is simpler than maximum likelihood and Johannessen explicitly uses it.

### Method of moments for 2-parameter Weibull

The mean and variance of a 2-parameter Weibull are:

$$\mu_W = \beta \cdot \Gamma\left(1 + \frac{1}{\alpha}\right)$$

$$\sigma^2_W = \beta^2 \left[\Gamma\left(1 + \frac{2}{\alpha}\right) - \Gamma\left(1 + \frac{1}{\alpha}\right)^2\right]$$

where Γ is the Gamma function. You observe μ_W and σ²_W from your data, then solve for α and β numerically.

### Code

```python
from scipy.special import gamma as gamma_func
from scipy.optimize import fsolve

def weibull_mom_equations(params, mean_obs, var_obs):
    """
    Equations to solve for Weibull parameters using method of moments.
    We want: theoretical mean = observed mean
             theoretical variance = observed variance
    """
    alpha, beta = params
    
    # Theoretical mean of Weibull
    mean_theory = beta * gamma_func(1 + 1/alpha)
    
    # Theoretical variance of Weibull
    var_theory = beta**2 * (gamma_func(1 + 2/alpha) - gamma_func(1 + 1/alpha)**2)
    
    # Return the difference - solver will find where this equals zero
    return [mean_theory - mean_obs, var_theory - var_obs]

# Compute observed mean and variance of W
mean_W = df_clean['W'].mean()
var_W = df_clean['W'].var()

print(f"Observed mean wind speed: {mean_W:.3f} m/s")
print(f"Observed variance of wind speed: {var_W:.3f} m²/s²")

# Solve for alpha and beta
# Initial guess: alpha=2, beta=mean (reasonable starting point for wind)
initial_guess = [2.0, mean_W]
alpha_W, beta_W = fsolve(weibull_mom_equations, initial_guess, 
                          args=(mean_W, var_W))

print(f"\nFitted Weibull parameters:")
print(f"  Shape (alpha): {alpha_W:.4f}")
print(f"  Scale (beta):  {beta_W:.4f} m/s")
print(f"\nJohannessen found: alpha=1.708, beta=8.426 (Northern North Sea)")
print(f"Difference is expected - your location is different")
```

### Validate the fit visually

This is what Johannessen does in Figure 1 of the paper — plotting observed CDF against the fitted Weibull CDF on probability paper.

```python
def weibull_cdf(w, alpha, beta):
    """Compute Weibull CDF at values w"""
    return 1 - np.exp(-(w / beta)**alpha)

# Sort your observed W values to get the empirical CDF
W_sorted = np.sort(df_clean['W'].values)
# Empirical CDF: the i-th sorted value has probability i/n of being exceeded
n = len(W_sorted)
empirical_cdf = np.arange(1, n+1) / n

# Theoretical CDF from your fitted Weibull
W_range = np.linspace(0.01, W_sorted.max() * 1.2, 500)
theoretical_cdf = weibull_cdf(W_range, alpha_W, beta_W)

# Plot - match Johannessen Figure 1 style
fig, ax = plt.subplots(figsize=(9, 6))

# Plot on log scale for x-axis (common for wind speed distributions)
ax.semilogx(W_sorted, empirical_cdf, 'ko', markersize=1.5, 
            alpha=0.3, label='ERA5 data')
ax.semilogx(W_range, theoretical_cdf, 'r-', linewidth=2, 
            label=f'Weibull fit (α={alpha_W:.3f}, β={beta_W:.3f})')

ax.set_xlabel('Wind Speed W (m/s)')
ax.set_ylabel('Probability of non-exceedance F(W)')
ax.set_title('Marginal Distribution of Wind Speed\n(cf. Johannessen Fig. 1)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('weibull_wind_fit.png', dpi=150)
plt.show()

# Quantify goodness of fit
# The fitted distribution should lie close to the data points
# Pay special attention to the upper tail (high wind speeds)
# because that is what drives your 100-year extreme

# Estimate 100-year wind speed from your fitted distribution
# 100-year return period at hourly resolution:
# Probability of exceedance per hour = 1 / (100 * 8766)
p_100yr = 1 / (100 * 8766)
# Find W such that 1 - F(W) = p_100yr, i.e. F(W) = 1 - p_100yr
W_100yr = beta_W * (-np.log(p_100yr))**(1/alpha_W)
print(f"\nEstimated 100-year wind speed: {W_100yr:.1f} m/s")
print(f"Johannessen found 39.0 m/s for Northern North Sea")
```

**What good looks like:** The red fitted line tracks the black data points closely, especially in the upper tail. If the upper tail diverges significantly, your fit is inadequate and you may need to try maximum likelihood estimation instead.

---

## STEP 3 — Fit the Conditional Distribution of Hs Given W

### What you are doing and why

This corresponds to the section **"CONDITIONAL DISTRIBUTION OF Hm0 FOR GIVEN W"** in the Johannessen paper. The paper states that a 2-parameter Weibull was chosen as the conditional distribution of Hs for a given wind speed.

The idea is: rather than one global distribution for Hs, you fit a separate Weibull to Hs *within each wind speed bin*. Then you model how the Weibull parameters change as W changes, so you can evaluate the distribution at any wind speed.

**Why bin by wind speed?** Because wave height physically depends on wind speed — calm winds produce small waves, strong winds produce large waves. If you fit one distribution to all Hs regardless of W, you lose this relationship. The conditional approach captures it explicitly.

### Code

```python
# Define wind speed bins
# Width of 2 m/s is typical - adjust based on your data range
W_max = df_clean['W'].max()
bin_edges = np.arange(0, W_max + 2, 2)  # 0-2, 2-4, 4-6, ...
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # midpoint of each bin

print(f"Wind speed range: 0 to {W_max:.1f} m/s")
print(f"Number of bins: {len(bin_edges)-1}")

# Fit Weibull to Hs within each wind speed bin
alpha_Hs_list = []
beta_Hs_list = []
W_bin_centers_used = []
n_per_bin = []

for i in range(len(bin_edges)-1):
    w_low = bin_edges[i]
    w_high = bin_edges[i+1]
    
    # Select Hs values where W falls in this bin
    mask = (df_clean['W'] >= w_low) & (df_clean['W'] < w_high)
    Hs_in_bin = df_clean.loc[mask, 'Hs'].values
    
    # Need at least ~50 points to fit a distribution reliably
    if len(Hs_in_bin) < 50:
        print(f"  Bin {w_low:.0f}-{w_high:.0f} m/s: only {len(Hs_in_bin)} points, skipping")
        continue
    
    # Fit 2-parameter Weibull using method of moments
    mean_Hs = Hs_in_bin.mean()
    var_Hs = Hs_in_bin.var()
    
    try:
        alpha_h, beta_h = fsolve(weibull_mom_equations, 
                                  [2.0, mean_Hs], 
                                  args=(mean_Hs, var_Hs))
        
        # Check the fit is physically reasonable
        if alpha_h > 0 and beta_h > 0:
            alpha_Hs_list.append(alpha_h)
            beta_Hs_list.append(beta_h)
            W_bin_centers_used.append(bin_centers[i])
            n_per_bin.append(len(Hs_in_bin))
            print(f"  Bin {w_low:.0f}-{w_high:.0f} m/s: "
                  f"n={len(Hs_in_bin)}, α={alpha_h:.3f}, β={beta_h:.3f}")
    except:
        print(f"  Bin {w_low:.0f}-{w_high:.0f} m/s: fitting failed")

# Convert to arrays
W_bin_centers_used = np.array(W_bin_centers_used)
alpha_Hs_arr = np.array(alpha_Hs_list)
beta_Hs_arr = np.array(beta_Hs_list)
```

### Fit smooth curves to how the parameters vary with W

You now have discrete estimates of α and β at each W bin centre. You need to fit smooth functions so you can evaluate the conditional distribution at any W value, including extreme values beyond your observations.

```python
# Fit smooth function: how does alpha_Hs vary with W?
# Try a simple power law: alpha(W) = c1 * W^c2 + c3
# Or a linear model - plot first to see the shape

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(W_bin_centers_used, alpha_Hs_arr, 'bo', markersize=8, label='Bin estimates')
axes[0].set_xlabel('Wind Speed W (m/s)')
axes[0].set_ylabel('Weibull shape α_Hs')
axes[0].set_title('How Hs Weibull shape varies with W')
axes[0].grid(True, alpha=0.3)

axes[1].plot(W_bin_centers_used, beta_Hs_arr, 'ro', markersize=8, label='Bin estimates')
axes[1].set_xlabel('Wind Speed W (m/s)')
axes[1].set_ylabel('Weibull scale β_Hs')
axes[1].set_title('How Hs Weibull scale varies with W')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('conditional_Hs_params.png', dpi=150)
plt.show()

# Based on what you see in the plot, choose an appropriate function
# Power law is a common choice:

def power_law(W, c1, c2, c3):
    return c1 * W**c2 + c3

# Fit alpha_Hs(W)
popt_alpha, _ = curve_fit(power_law, W_bin_centers_used, alpha_Hs_arr, 
                           p0=[1, 0.5, 0.5], maxfev=10000)

# Fit beta_Hs(W)  
popt_beta, _ = curve_fit(power_law, W_bin_centers_used, beta_Hs_arr, 
                          p0=[0.1, 1.5, 0.0], maxfev=10000)

print("Fitted smooth functions for Hs Weibull parameters:")
print(f"  alpha_Hs(W) = {popt_alpha[0]:.4f} * W^{popt_alpha[1]:.4f} + {popt_alpha[2]:.4f}")
print(f"  beta_Hs(W)  = {popt_beta[0]:.4f} * W^{popt_beta[1]:.4f} + {popt_beta[2]:.4f}")

# Define functions you will reuse later
def alpha_Hs_func(W):
    return power_law(W, *popt_alpha)

def beta_Hs_func(W):
    return power_law(W, *popt_beta)

# Plot the smooth fits over your bin estimates
W_plot = np.linspace(W_bin_centers_used.min(), W_bin_centers_used.max() * 1.3, 200)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(W_bin_centers_used, alpha_Hs_arr, 'bo', label='Bin estimates', markersize=8)
axes[0].plot(W_plot, alpha_Hs_func(W_plot), 'b-', linewidth=2, label='Smooth fit')
axes[0].set_xlabel('W (m/s)'); axes[0].set_ylabel('α_Hs'); axes[0].legend()
axes[0].set_title('Hs shape parameter vs W')

axes[1].plot(W_bin_centers_used, beta_Hs_arr, 'ro', label='Bin estimates', markersize=8)
axes[1].plot(W_plot, beta_Hs_func(W_plot), 'r-', linewidth=2, label='Smooth fit')
axes[1].set_xlabel('W (m/s)'); axes[1].set_ylabel('β_Hs'); axes[1].legend()
axes[1].set_title('Hs scale parameter vs W')

plt.tight_layout()
plt.savefig('Hs_smooth_params.png', dpi=150)
plt.show()
```

**What you are looking for:** The smooth curves should follow the general trend of the bin estimates. They should not wiggle or behave strangely at large W values (extrapolation region), because that is where your extremes will come from.

### Helper function: the conditional CDF of Hs given W

```python
def F_Hs_given_W(h, w):
    """
    CDF of Hs given W: probability that wave height <= h when wind speed is w
    Uses the fitted smooth Weibull parameters
    """
    alpha = alpha_Hs_func(w)
    beta = beta_Hs_func(w)
    return 1 - np.exp(-(h / beta)**alpha)

def f_Hs_given_W(h, w):
    """
    PDF of Hs given W (probability density, used for plotting/verification)
    """
    alpha = alpha_Hs_func(w)
    beta = beta_Hs_func(w)
    return (alpha / beta) * (h / beta)**(alpha - 1) * np.exp(-(h / beta)**alpha)
```

---

## STEP 4 — Fit the Conditional Distribution of Tp Given Hs and W

### What you are doing and why

This corresponds to the **"CONDITIONAL DISTRIBUTION OF Tp"** section. The MDPI 2023 paper (Section 3.3) describes this in full detail — Johannessen's paper cuts off before reaching it, but the MDPI paper implements the same approach.

The MDPI paper states: *"The Lognormal distribution proves to be more amenable considering these aspects"* — specifically because its two parameters (mean and variance of ln(Tp)) can be extrapolated smoothly beyond observed data using simple parametric functions, which is essential because your 100-year return period analysis will require evaluating the distribution at (W, Hs) combinations you have never actually observed.

The Lognormal says: ln(Tp) is normally distributed. So instead of working with Tp directly, you work with ln(Tp), which is simpler.

The two parameters of the conditional Lognormal are modelled as:

$$\mu_{\ln T_p}(h, w) = a_1 + a_2 \cdot h^{a_3}$$
$$\sigma^2_{\ln T_p}(h, w) = b_1 + b_2 \cdot \exp(-b_3 \cdot h)$$

These are equations (14) and (15) from the MDPI 2023 paper. You fit separate sets of (a1, a2, a3, b1, b2, b3) for each wind speed bin.

**Why these functional forms?**
- The mean of ln(Tp) increases with Hs (larger waves tend to have longer periods) but flattens out at large Hs — a power law captures this
- The variance of ln(Tp) tends to *decrease* with Hs (in very extreme conditions, Tp and Hs are more tightly coupled) — the decaying exponential captures this

### Code

```python
# For each wind speed bin, further bin by Hs and fit Lognormal to Tp

# We will store fitted Lognormal parameter functions for each W bin
lognormal_params = {}  # key = W bin center, value = dict of fitted coefficients

for i, w_center in enumerate(W_bin_centers_used):
    w_low = bin_edges[i] if i < len(bin_edges)-1 else w_center - 1
    # Recalculate bin edges for this wind bin
    # (Use the same binning as before)
    w_low_val = w_center - 1.0  # approximate half-bin width
    w_high_val = w_center + 1.0
    
    # Select data in this wind bin
    mask_w = (df_clean['W'] >= w_low_val) & (df_clean['W'] < w_high_val)
    df_wind_bin = df_clean[mask_w]
    
    if len(df_wind_bin) < 100:
        continue
    
    # Now bin by Hs within this wind bin
    Hs_max_in_bin = df_wind_bin['Hs'].max()
    Hs_bin_edges = np.arange(0, Hs_max_in_bin + 1.0, 1.0)  # 1m bins
    Hs_bin_centers = (Hs_bin_edges[:-1] + Hs_bin_edges[1:]) / 2
    
    mu_lnTp_list = []
    var_lnTp_list = []
    Hs_centers_used = []
    
    for j in range(len(Hs_bin_edges)-1):
        h_low = Hs_bin_edges[j]
        h_high = Hs_bin_edges[j+1]
        
        mask_h = (df_wind_bin['Hs'] >= h_low) & (df_wind_bin['Hs'] < h_high)
        Tp_in_cell = df_wind_bin.loc[mask_h, 'Tp'].values
        
        if len(Tp_in_cell) < 30:
            continue
        
        # Compute mean and variance of ln(Tp)
        lnTp = np.log(Tp_in_cell)
        mu_lnTp_list.append(lnTp.mean())
        var_lnTp_list.append(lnTp.var())
        Hs_centers_used.append(Hs_bin_centers[j])
    
    if len(Hs_centers_used) < 4:
        continue
    
    Hs_centers_arr = np.array(Hs_centers_used)
    mu_arr = np.array(mu_lnTp_list)
    var_arr = np.array(var_lnTp_list)
    
    # Fit smooth functions - equations (14) and (15) from MDPI 2023 paper
    
    # mu_lnTp(h) = a1 + a2 * h^a3
    def mu_func(h, a1, a2, a3):
        return a1 + a2 * h**a3
    
    # sigma2_lnTp(h) = b1 + b2 * exp(-b3 * h)
    def var_func(h, b1, b2, b3):
        return b1 + b2 * np.exp(-b3 * h)
    
    try:
        popt_mu, _ = curve_fit(mu_func, Hs_centers_arr, mu_arr, 
                                p0=[1.5, 0.1, 0.5], maxfev=10000)
        
        # Ensure variance stays positive - add bounds
        popt_var, _ = curve_fit(var_func, Hs_centers_arr, var_arr,
                                 p0=[0.01, 0.1, 0.5], 
                                 bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
                                 maxfev=10000)
        
        lognormal_params[w_center] = {
            'popt_mu': popt_mu,
            'popt_var': popt_var,
            'Hs_centers': Hs_centers_arr,
            'mu_obs': mu_arr,
            'var_obs': var_arr
        }
        
        print(f"W bin ~{w_center:.0f} m/s: mu params={popt_mu}, var params={popt_var}")
        
    except Exception as e:
        print(f"W bin ~{w_center:.0f} m/s: fitting failed - {e}")
```

### Validate by plotting (following MDPI Figure 3)

```python
# Plot the smooth parameter fits for a mid-range wind bin
# Choose a W bin that has good data coverage

w_example = W_bin_centers_used[len(W_bin_centers_used)//2]  # middle bin

if w_example in lognormal_params:
    params = lognormal_params[w_example]
    Hs_plot = np.linspace(0.1, params['Hs_centers'].max() * 1.5, 200)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Mean of ln(Tp)
    mu_smooth = mu_func(Hs_plot, *params['popt_mu'])
    axes[0].plot(params['Hs_centers'], params['mu_obs'], 'bo', 
                 label='Bin estimates', markersize=8)
    axes[0].plot(Hs_plot, mu_smooth, 'b-', linewidth=2, label='Smooth fit')
    axes[0].set_xlabel('Hs (m)')
    axes[0].set_ylabel('μ_ln(Tp)')
    axes[0].set_title(f'Mean of ln(Tp) | W ≈ {w_example:.0f} m/s\n(cf. MDPI 2023 Fig. 3)')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)
    
    # Variance of ln(Tp)
    var_smooth = var_func(Hs_plot, *params['popt_var'])
    axes[1].plot(params['Hs_centers'], params['var_obs'], 'ro', 
                 label='Bin estimates', markersize=8)
    axes[1].plot(Hs_plot, var_smooth, 'r-', linewidth=2, label='Smooth fit')
    axes[1].set_xlabel('Hs (m)')
    axes[1].set_ylabel('σ²_ln(Tp)')
    axes[1].set_title(f'Variance of ln(Tp) | W ≈ {w_example:.0f} m/s')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lognormal_Tp_params.png', dpi=150)
    plt.show()
```

### Helper function: conditional CDF of Tp given Hs and W

```python
def get_lognormal_params_for_Wbin(w):
    """Find the nearest fitted W bin and return its parameter functions"""
    # Find nearest W bin center
    w_centers = np.array(list(lognormal_params.keys()))
    nearest_idx = np.argmin(np.abs(w_centers - w))
    return lognormal_params[w_centers[nearest_idx]]

def F_Tp_given_Hs_W(t, h, w):
    """
    CDF of Tp given Hs and W.
    Returns probability that peak period <= t, given wave height h and wind speed w.
    """
    params = get_lognormal_params_for_Wbin(w)
    
    # Get smooth parameter values at this Hs
    mu = mu_func(h, *params['popt_mu'])
    sigma2 = var_func(h, *params['popt_var'])
    sigma2 = max(sigma2, 0.001)  # enforce minimum variance as per MDPI paper
    sigma = np.sqrt(sigma2)
    
    # Lognormal CDF: probability that Tp <= t
    # = probability that ln(Tp) <= ln(t)
    # = standard normal CDF of (ln(t) - mu) / sigma
    return stats.norm.cdf((np.log(t) - mu) / sigma)
```

---

## STEP 5 — The Rosenblatt Transformation (Going to Standard Normal Space)

### What you are doing and why

This is the step that connects your joint distribution to the contour surface. The IFORM method (used to construct the contour surface) requires that your variables be expressed in **standard normal space** — a space where each variable is independent and normally distributed with mean 0 and variance 1.

The Rosenblatt transformation converts your correlated physical variables (W, Hs, Tp) into independent standard normal variables (U1, U2, U3). The transformation uses your fitted conditional CDFs to do this:

$$U_1 = \Phi^{-1}(F_W(w))$$
$$U_2 = \Phi^{-1}(F_{H_s|W}(h|w))$$
$$U_3 = \Phi^{-1}(F_{T_p|H_s,W}(t|h,w))$$

where Φ⁻¹ is the inverse of the standard normal CDF (also called the probit function).

**Why does this work?** Because F_W(w) is a probability between 0 and 1. Applying Φ⁻¹ to a uniform [0,1] random variable gives you a standard normal variable. The chain of conditional CDFs preserves the dependence structure while standardising everything.

**The inverse direction** (from U-space back to physical space) is what you use to construct the contour:

$$w = F_W^{-1}(\Phi(U_1))$$
$$h = F_{H_s|W}^{-1}(\Phi(U_2) | w)$$
$$t = F_{T_p|H_s,W}^{-1}(\Phi(U_3) | h, w)$$

### Code

```python
from scipy.stats import norm
from scipy.optimize import brentq

def W_to_U1(w):
    """Transform physical wind speed to standard normal U1"""
    p = weibull_cdf(w, alpha_W, beta_W)
    p = np.clip(p, 1e-10, 1 - 1e-10)  # avoid log(0) in norm.ppf
    return norm.ppf(p)

def U1_to_W(u1):
    """Inverse: transform U1 back to physical wind speed"""
    p = norm.cdf(u1)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    # Invert Weibull CDF: W = beta * (-ln(1-p))^(1/alpha)
    return beta_W * (-np.log(1 - p))**(1/alpha_W)

def Hs_to_U2(h, w):
    """Transform physical wave height to standard normal U2 (conditional on W=w)"""
    p = F_Hs_given_W(h, w)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    return norm.ppf(p)

def U2_to_Hs(u2, w):
    """Inverse: transform U2 back to physical wave height given W=w"""
    p = norm.cdf(u2)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    # Invert conditional Weibull CDF
    alpha = alpha_Hs_func(w)
    beta = beta_Hs_func(w)
    return beta * (-np.log(1 - p))**(1/alpha)

def Tp_to_U3(t, h, w):
    """Transform physical peak period to standard normal U3 (conditional on Hs=h, W=w)"""
    p = F_Tp_given_Hs_W(t, h, w)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    return norm.ppf(p)

def U3_to_Tp(u3, h, w):
    """Inverse: transform U3 back to physical peak period given Hs=h, W=w"""
    p = norm.cdf(u3)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    params = get_lognormal_params_for_Wbin(w)
    mu = mu_func(h, *params['popt_mu'])
    sigma2 = max(var_func(h, *params['popt_var']), 0.001)
    sigma = np.sqrt(sigma2)
    # Invert Lognormal: Tp = exp(mu + sigma * Phi^-1(p))
    return np.exp(mu + sigma * norm.ppf(p))
```

---

## STEP 6 — Build the 100-Year Contour Surface (IFORM)

### What you are doing and why

In standard normal space (U1, U2, U3), the joint distribution of independent standard normals is spherically symmetric. The probability of falling *outside* a sphere of radius β is the same in all directions. This is the key insight of IFORM.

For a 100-year return period at **hourly** resolution:

$$p = \frac{1}{100 \times 8766} \approx 1.14 \times 10^{-6}$$

$$\beta = \Phi^{-1}(1 - p) \approx 4.75$$

Every point on the sphere U1² + U2² + U3² = β² in standard normal space corresponds to a combination of (W, Hs, Tp) in physical space with the same 100-year return probability. You parametrise the sphere using spherical angles, generate points on it, then back-transform to physical space.

```python
# Compute the target reliability index beta for 100-year return period
# At hourly resolution: 100 years * 8766 hours/year
K1Y_hourly = 8766  # number of hourly observations per year
return_period = 100  # years

p_exceedance = 1 / (return_period * K1Y_hourly)
beta_target = norm.ppf(1 - p_exceedance)

print(f"100-year return period probability per hour: {p_exceedance:.2e}")
print(f"Target reliability index beta: {beta_target:.4f}")
# You should get approximately 4.75

# Parametrise the sphere in U-space using spherical coordinates
# U1 = beta * cos(theta)
# U2 = beta * sin(theta) * cos(phi)
# U3 = beta * sin(theta) * sin(phi)

n_theta = 50  # resolution in polar angle (0 to pi)
n_phi = 100   # resolution in azimuthal angle (0 to 2*pi)

theta_vals = np.linspace(0.01, np.pi - 0.01, n_theta)
phi_vals = np.linspace(0, 2*np.pi, n_phi)

# Storage for the contour surface in physical space
W_contour = np.zeros((n_theta, n_phi))
Hs_contour = np.zeros((n_theta, n_phi))
Tp_contour = np.zeros((n_theta, n_phi))

print("Building contour surface - this may take a few minutes...")

for i, theta in enumerate(theta_vals):
    for j, phi in enumerate(phi_vals):
        
        # Point on the sphere in U-space
        u1 = beta_target * np.cos(theta)
        u2 = beta_target * np.sin(theta) * np.cos(phi)
        u3 = beta_target * np.sin(theta) * np.sin(phi)
        
        # Back-transform to physical space
        try:
            w = U1_to_W(u1)
            h = U2_to_Hs(u2, w)
            t = U3_to_Tp(u3, h, w)
            
            W_contour[i, j] = w
            Hs_contour[i, j] = h
            Tp_contour[i, j] = t
            
        except Exception:
            # Some points may fail numerically at extremes
            W_contour[i, j] = np.nan
            Hs_contour[i, j] = np.nan
            Tp_contour[i, j] = np.nan

print("Contour surface complete.")
print(f"\nMax W on contour:  {np.nanmax(W_contour):.1f} m/s")
print(f"Max Hs on contour: {np.nanmax(Hs_contour):.1f} m")
print(f"Max Tp on contour: {np.nanmax(Tp_contour):.1f} s")
```

---

## STEP 7 — Visualise and Interpret the Contour Surface

### 3D surface plot

```python
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Flatten and remove NaN values for plotting
mask = ~(np.isnan(W_contour) | np.isnan(Hs_contour) | np.isnan(Tp_contour))

sc = ax.scatter(W_contour[mask], Hs_contour[mask], Tp_contour[mask],
                c=Tp_contour[mask], cmap='viridis', 
                alpha=0.4, s=5)

plt.colorbar(sc, ax=ax, label='Peak Period Tp (s)', pad=0.1)
ax.set_xlabel('Wind Speed W (m/s)')
ax.set_ylabel('Wave Height Hs (m)')
ax.set_zlabel('Peak Period Tp (s)')
ax.set_title('100-Year Environmental Contour Surface\n(cf. Johannessen et al. 2002)')

plt.tight_layout()
plt.savefig('contour_surface_3D.png', dpi=150)
plt.show()
```

### 2D slices — more useful for engineering decisions

```python
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Hs vs Tp (collapsing over W) - scatter all contour points
axes[0].scatter(Tp_contour[mask], Hs_contour[mask], 
                c=W_contour[mask], cmap='plasma', s=5, alpha=0.5)
axes[0].set_xlabel('Peak Period Tp (s)')
axes[0].set_ylabel('Significant Wave Height Hs (m)')
axes[0].set_title('Hs vs Tp on 100-year contour\n(colour = wind speed)')
axes[0].grid(True, alpha=0.3)
sm = plt.cm.ScalarMappable(cmap='plasma')
sm.set_array(W_contour[mask])
plt.colorbar(sm, ax=axes[0], label='W (m/s)')

# Plot 2: W vs Hs
axes[1].scatter(W_contour[mask], Hs_contour[mask], 
                c=Tp_contour[mask], cmap='viridis', s=5, alpha=0.5)
axes[1].set_xlabel('Wind Speed W (m/s)')
axes[1].set_ylabel('Significant Wave Height Hs (m)')
axes[1].set_title('W vs Hs on 100-year contour\n(colour = peak period)')
axes[1].grid(True, alpha=0.3)

# Plot 3: W vs Tp
axes[2].scatter(W_contour[mask], Tp_contour[mask], 
                c=Hs_contour[mask], cmap='coolwarm', s=5, alpha=0.5)
axes[2].set_xlabel('Wind Speed W (m/s)')
axes[2].set_ylabel('Peak Period Tp (s)')
axes[2].set_title('W vs Tp on 100-year contour\n(colour = wave height)')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('contour_surface_2D_slices.png', dpi=150)
plt.show()
```

### Extract 100-year design values

```python
# Find the most extreme point on the contour for each variable individually
print("=" * 50)
print("100-YEAR DESIGN VALUES FROM CONTOUR SURFACE")
print("=" * 50)

# Maximum wind speed on contour
idx_max_W = np.nanargmax(W_contour)
print(f"\nPoint of maximum wind speed on contour:")
print(f"  W  = {W_contour.flat[idx_max_W]:.2f} m/s")
print(f"  Hs = {Hs_contour.flat[idx_max_W]:.2f} m")
print(f"  Tp = {Tp_contour.flat[idx_max_W]:.2f} s")

# Maximum wave height on contour
idx_max_Hs = np.nanargmax(Hs_contour)
print(f"\nPoint of maximum wave height on contour:")
print(f"  W  = {W_contour.flat[idx_max_Hs]:.2f} m/s")
print(f"  Hs = {Hs_contour.flat[idx_max_Hs]:.2f} m")
print(f"  Tp = {Tp_contour.flat[idx_max_Hs]:.2f} s")

# Maximum peak period on contour
idx_max_Tp = np.nanargmax(Tp_contour)
print(f"\nPoint of maximum peak period on contour:")
print(f"  W  = {W_contour.flat[idx_max_Tp]:.2f} m/s")
print(f"  Hs = {Hs_contour.flat[idx_max_Tp]:.2f} m")
print(f"  Tp = {Tp_contour.flat[idx_max_Tp]:.2f} s")
```

---

## Summary: What Each Step Is Doing and Where It Comes From

| Step | What | Paper reference |
|---|---|---|
| 1 | Extract W, Hs, Tp from ERA5 | Your data replaces Johannessen's composite measurements |
| 2 | Weibull fit to W | Johannessen §"Marginal Distribution for Wind, W", eq. (2) |
| 3 | Conditional Weibull for Hs\|W | Johannessen §"Conditional Distribution of Hm0 for given W" |
| 4 | Conditional Lognormal for Tp\|Hs,W | MDPI 2023 §3.3, eqs. (13)–(15) |
| 5 | Rosenblatt transformation | Standard IFORM theory (implemented in both papers) |
| 6 | Sphere in U-space, back-transform | IFORM method — produces the contour surface |
| 7 | Visualise and extract design values | Equivalent to Johannessen's Figure showing the contour surface |


