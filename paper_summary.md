Sure. Here's the full picture of what the paper did, step by step.

The Big Question
"Is the IEA 15 MW floating wind turbine structurally safe under the worst 100-year sea conditions?"

To answer that, they needed to:

Figure out what the worst realistic combination of wind + waves looks like
Simulate the turbine under those conditions
Check if the structure survives
Step 1 — Build the 3D Environmental Contour
The ocean has three things that stress the turbine simultaneously:

Wind speed $U_w$ (at 10 m above sea level)
Significant wave height $H_s$ (how tall the waves are)
Peak wave period $T_p$ (how fast the waves come)
These three aren't independent — strong winds come with big waves, big waves tend to have longer periods, etc. The paper used statistical distributions from 26 years of North Sea data (Johannessen et al. 2001) to model how they're linked:

Variable	Distribution	Depends on
$U_w$	Weibull	— (marginal)
$H_s$	Weibull	$U_w$
$T_p$	Lognormal	$H_s$ and $U_w$
Then they used a method called IFORM (Inverse First-Order Reliability Method) to find all combinations of $(U_w, H_s, T_p)$ that are equally rare — specifically, all combinations with a 100-year return period.

The result is a 3D surface (their Fig. 2 — which you've already reproduced). Every point on that surface is a different "equally dangerous" storm.

Step 2 — Slice the 3D Surface into 2D Contours
Running a full 3D simulation for every point on that surface would take forever. So they sliced it.

They picked 4 specific wind speeds at the hub (150 m height):

Hub speed	What it represents
6.98 m/s	Cut-in speed — turbine just starts
10.59 m/s	Rated speed — maximum power output
25 m/s	Cut-out speed — turbine shuts down
57.64 m/s	100-year extreme wind — turbine is parked
For each fixed wind speed, they sliced through the 3D contour surface and got a 2D loop in $(H_s, T_p)$ space (their Fig. 3). Each loop says: "at this wind speed, these are all the wave combinations that are equally rare."

Step 3 — Pick the Worst Point on Each 2D Contour
Not every point on the 2D contour stresses the turbine equally. So they ran OpenFAST simulations at multiple points around each loop and found which combination of $(H_s, T_p)$ produced the largest structural responses (mooring tension, tower shear force, bending moment).

The worst-case conditions they found were (Table 8):

Case	$H_s$ (m)	$T_p$ (s)	Hub wind (m/s)	Turbine state
EC1	6.06	12.50	3	Operating
EC2	6.80	12.70	6.89	Operating
EC3	7.28	12.34	10.59	Operating
EC4	10.46	14.12	25	Operating
EC5	14.33	14.78	57.64	Parked
Step 4 — Simulate the Turbine Under Those 5 Conditions
For each of the 5 extreme conditions (EC1–EC5), they ran 50 simulations of 3600 seconds each (1 hour) using OpenFAST. That gives 50 time series of things like:

Tension in each mooring cable
Shear force at the tower base
Bending moment at the tower base
Step 5 — Predict the Extreme Values (Two Methods)
From those 50 time series, they needed to estimate the single worst value the structure would ever experience. They used two statistical methods:

Gumbel method — takes the maximum of each simulation, fits a Gumbel distribution, extrapolates to find the 1% exceedance value. Simple but slightly conservative.

ACER method — takes all peaks from each simulation, accounts for statistical dependence between consecutive peaks (Markov-like), fits a tail model. More accurate but more complex.

Both methods agreed reasonably well, with ACER giving slightly lower (less conservative) predictions.

Step 6 — Safety Check
Finally they asked: do the predicted extreme loads exceed the allowable limits?

For mooring lines: maximum tension must be < 60% of breaking strength (API-RP-2SK standard). They found the maximum tension was 4.74 × 10³ kN, giving a safety factor of 4.70 — well above the minimum of 1.67. ✓

For tower base: shear force and bending moment must be within the structural capacity of S355 steel (Eurocode 3). Both were within limits. ✓

The Key Finding
EC5 (parked turbine in 57.64 m/s wind + 14.3 m waves) produced the largest tower loads, even though the turbine was shut down. This is because at that wind speed the turbine is parked — the wind hits the tower and platform directly with nothing to absorb it, generating huge thrust on the structure.

This is counterintuitive — you might expect the operating turbine (spinning blades converting wind to electricity) to be under more stress, but the parked case is actually worse for structural loads.