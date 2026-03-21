"""
Generate meeting slides for PhD supervisor meeting.
Follows meeting_slides_notes.md exactly.
Produces: meeting_slides.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

DEMO_OUT = os.path.join(os.path.dirname(__file__), "demo_out")

DARK_BLUE  = RGBColor(0x1A, 0x37, 0x5E)
MID_BLUE   = RGBColor(0x2E, 0x6D, 0xA4)
LIGHT_BLUE = RGBColor(0xEB, 0xF3, 0xFB)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x22, 0x22, 0x22)
ORANGE     = RGBColor(0xE8, 0x6A, 0x1A)
GREY_TEXT  = RGBColor(0x88, 0x88, 0x88)
BLUE_DIM   = RGBColor(0xBB, 0xCC, 0xDD)
CREAM      = RGBColor(0xFF, 0xF8, 0xF0)
PALE_GREEN = RGBColor(0xEA, 0xF5, 0xEA)
GREEN      = RGBColor(0x1A, 0x7A, 0x3C)


# ── helpers ───────────────────────────────────────────────────────────────────

def slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def bg(s, color):
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = color


def rect(s, l, t, w, h, fill=None, line=None):
    sh = s.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = line
    else:
        sh.line.fill.background()
    return sh


def text(s, txt, l, t, w, h, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = txt
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return tb


def bullets(s, items, l, t, w, h, size=13, title=None, tsize=14,
            color=BLACK, tcolor=MID_BLUE, spacing=None):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    first = True
    if title:
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = title
        r.font.size = Pt(tsize); r.font.bold = True; r.font.color.rgb = tcolor
        first = False
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if spacing:
            from pptx.util import Pt as PPt
            p.space_before = PPt(spacing)
        r = p.add_run(); r.text = "• " + item
        r.font.size = Pt(size); r.font.color.rgb = color
    return tb


def header(s, title, subtitle=None):
    rect(s, 0, 0, 10, 1.3, fill=DARK_BLUE)
    text(s, title, 0.25, 0.1, 9.5, 0.7, size=25, bold=True, color=WHITE)
    if subtitle:
        text(s, subtitle, 0.25, 0.76, 9.5, 0.42, size=13, color=BLUE_DIM)


def footer(s, txt="PhD Supervisor Meeting  |  March 2026"):
    text(s, txt, 0, 7.3, 10, 0.35, size=9, color=GREY_TEXT, align=PP_ALIGN.CENTER)


def img(s, fname, l, t, w=None, h=None):
    path = os.path.join(DEMO_OUT, fname)
    if not os.path.exists(path):
        return
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    s.shapes.add_picture(path, Inches(l), Inches(t), **kw)


def stat(s, label, value, x, y, w=2.1, h=0.9,
         bg_c=LIGHT_BLUE, border=MID_BLUE, vcolor=DARK_BLUE):
    rect(s, x, y, w, h, fill=bg_c, line=border)
    text(s, label, x+0.08, y+0.05, w-0.15, 0.3, size=10, color=GREY_TEXT, align=PP_ALIGN.CENTER)
    text(s, value, x+0.08, y+0.36, w-0.15, 0.45, size=17, bold=True, color=vcolor, align=PP_ALIGN.CENTER)


# ── build ─────────────────────────────────────────────────────────────────────

prs = Presentation()
prs.slide_width  = Inches(10)
prs.slide_height = Inches(7.5)


# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs)
rect(s, 0, 0, 10, 7.5, fill=DARK_BLUE)
rect(s, 0, 2.7, 10, 2.3, fill=MID_BLUE)
text(s, "ERA5-Based Extreme Wind Analysis",
     0.5, 0.85, 9.0, 1.1, size=34, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
text(s, "Hub-Height Extrapolation, Shear Sensitivity & Extreme-Value Methods",
     0.5, 2.0, 9.0, 0.6, size=16, color=BLUE_DIM, align=PP_ALIGN.CENTER)
text(s, "PhD Supervisor Meeting  ·  March 2026",
     0.5, 2.85, 9.0, 0.45, size=15, color=WHITE, align=PP_ALIGN.CENTER)
text(s, "Data: ERA5 reanalysis  ·  Target: IEA 15 MW, Northern North Sea",
     0.5, 3.42, 9.0, 0.5, size=13, color=RGBColor(0xCC,0xDD,0xEE), align=PP_ALIGN.CENTER)
text(s, "Preliminary results — not final thesis values",
     0.5, 6.9, 9.0, 0.38, size=11, color=ORANGE, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — NOTES SLIDE 1: Objective
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Objective & Current Scope",
       "ERA5-based extreme wind workflow and paper replication plan")

bullets(s,
    ["Replication target: Chai et al. (2024) — short-term extreme structural responses for the IEA 15 MW offshore wind turbine",
     "Immediate goal: build a defensible preliminary ERA5 workflow to test hub-height extrapolation and several extreme-value methods on real data",
     "This is a working first step — not yet the full wind-wave contour replication"],
    0.4, 1.45, 9.2, 2.1, title="What this work is", size=14, tsize=15, spacing=4)

rect(s, 0.4, 3.62, 9.2, 0.04, fill=MID_BLUE)

bullets(s,
    ["ERA5 data coverage: 1950-01-01  →  1981-03-31  (downloaded so far)",
     "ERA5 files contain both wind and wave fields — winds and wave variables have been unpacked and are available",
     "Analysis shown today is focused on wind only — the joint wind-wave environmental model comes next",
     "Full replication still requires: joint wind-wave model, environmental contours, OpenFAST response runs"],
    0.4, 3.75, 9.2, 2.65, title="Current status", size=14, tsize=15, spacing=4)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — NOTES SLIDE 2a: The formula
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Hub-Height Wind Extrapolation",
       "The power-law formula used to estimate wind speed at 150 m")

# large formula box
rect(s, 0.4, 1.45, 9.2, 1.7, fill=LIGHT_BLUE, line=MID_BLUE)
text(s, "U_hub  =  U_ref  ×  ( z_hub / z_ref ) ^ α",
     0.65, 1.58, 8.8, 0.6, size=22, bold=True, color=DARK_BLUE, align=PP_ALIGN.CENTER)
text(s, "V_hub,10min  =  1.10  ×  U_hub",
     0.65, 2.18, 8.8, 0.55, size=20, bold=True, color=MID_BLUE, align=PP_ALIGN.CENTER)

# term definitions
bullets(s,
    ["U_ref  — wind speed known from ERA5 at the reference height (either 10 m or 100 m above sea level)",
     "z_ref  — the reference height where ERA5 measures the wind (10 m or 100 m)",
     "z_hub  — hub height of the turbine: 150 m for the IEA 15 MW",
     "α      — the wind-shear exponent, controls how steeply wind increases with height",
     "1.10   — the paper's scaling factor converting a 1-hour mean to a 10-minute mean hub-height wind"],
    0.4, 3.28, 9.2, 3.0, title="What each term means", size=13, tsize=14, spacing=2)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — NOTES SLIDE 2b: Physical intuition
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Why Wind Speed Increases with Height",
       "Physical intuition behind the power-law shear formula")

bullets(s,
    ["Near the sea surface, friction between the air and water slows the wind down",
     "Higher up, that surface drag weakens — wind becomes faster and more uniform",
     "The power-law formula captures this vertical increase using the exponent α",
     "Smaller α  →  weaker shear, less increase with height  (common offshore over smooth sea surface)",
     "Larger α   →  stronger shear, more increase with height  (more typical over land or rougher terrain)"],
    0.4, 1.45, 9.2, 3.1, title="Intuition", size=14, tsize=15, spacing=5)

rect(s, 0.4, 4.62, 9.2, 0.04, fill=MID_BLUE)

# alpha = 0.11 rationale
bullets(s,
    ["The paper explicitly uses α = 0.11 as its baseline",
     "This is a relatively low, offshore-type shear assumption — appropriate for open-sea conditions",
     "Using the same α = 0.11 keeps this analysis consistent with the paper before introducing any sensitivity tests"],
    0.4, 4.75, 9.2, 1.95, title="Why α = 0.11?", size=14, tsize=15, spacing=5)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — NOTES SLIDE 2c: Two paths
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Two Extrapolation Paths to Hub Height",
       "Paper-consistent baseline from 10 m, plus an ERA5 sensitivity check from 100 m")

# Path A
rect(s, 0.3, 1.45, 4.4, 3.5, fill=LIGHT_BLUE, line=MID_BLUE)
text(s, "Path A  —  from 10 m", 0.48, 1.52, 4.1, 0.4, size=14, bold=True, color=DARK_BLUE)
text(s, "U_hub = U₁₀ × (150 / 10) ^ α\nV_hub,10min = 1.10 × U_hub",
     0.48, 1.98, 4.1, 0.85, size=14, bold=True, color=DARK_BLUE)
bullets(s,
    ["10 m is the reference height used in the paper's environmental model",
     "Paper-consistent baseline — used as the primary result",
     "Large vertical jump: 10 m → 150 m (factor of 15)"],
    0.48, 2.9, 4.05, 1.9, size=13, spacing=4)

# Path B
rect(s, 5.0, 1.45, 4.4, 3.5, fill=CREAM, line=ORANGE)
text(s, "Path B  —  from 100 m", 5.18, 1.52, 4.1, 0.4, size=14, bold=True, color=ORANGE)
text(s, "U_hub = U₁₀₀ × (150 / 100) ^ α\nV_hub,10min = 1.10 × U_hub",
     5.18, 1.98, 4.1, 0.85, size=14, bold=True, color=ORANGE)
bullets(s,
    ["ERA5 also provides 100 m wind directly",
     "Sensitivity check — not the primary result",
     "Small vertical jump: 100 m → 150 m (factor of 1.5)"],
    5.18, 2.9, 4.05, 1.9, size=13, spacing=4)

rect(s, 0.3, 5.08, 9.1, 0.04, fill=DARK_BLUE)
text(s,
    "Because Path B spans a much smaller height range, it is far less sensitive "
    "to the assumed value of α — making it a useful sensitivity benchmark.",
    0.3, 5.18, 9.45, 0.7, size=13, color=DARK_BLUE, align=PP_ALIGN.LEFT)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — NOTES SLIDE 3a: Monthly mean comparison
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Monthly Mean Hub-Height Wind — Both Paths Compared",
       "Path A (from 10 m) vs Path B (from 100 m)")

img(s, "fig_monthly_mean_vhub_compare.png", 0.3, 1.42, w=9.4)

bullets(s,
    ["Each point on the chart is the monthly mean of the area-averaged hub-height 10-min wind speed",
     "The two lines track each other closely in shape — both rise and fall together seasonally",
     "Path A (10 m) sits consistently above Path B (100 m) by roughly 0.8–1 m/s on average",
     "This is a systematic offset, not random scatter — it comes from the larger height extrapolation in Path A"],
    0.3, 5.52, 9.4, 1.72, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — NOTES SLIDE 3b: Mean summary bar + key numbers
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Average Hub-Height Wind — Summary",
       "Overall mean comparison and key statistics")

img(s, "fig_extrapolation_means_bar.png", 0.3, 1.42, w=5.3)

stat(s, "Path A mean\n(from 10 m)", "12.37 m/s", 5.85, 1.55, w=3.8, h=1.05,
     bg_c=LIGHT_BLUE, border=MID_BLUE)
stat(s, "Path B mean\n(from 100 m)", "11.55 m/s", 5.85, 2.72, w=3.8, h=1.05,
     bg_c=CREAM, border=ORANGE, vcolor=ORANGE)
stat(s, "Mean absolute\ndifference", "0.96 m/s", 5.85, 3.89, w=3.8, h=1.05,
     bg_c=LIGHT_BLUE, border=DARK_BLUE)

rect(s, 0.3, 5.12, 9.4, 0.04, fill=MID_BLUE)
text(s,
    "The ~0.8 m/s systematic difference between the two paths is not negligible "
    "— it is large enough to affect return-level estimates. "
    "The question is: which estimate is closer to reality?",
    0.3, 5.22, 9.4, 0.75, size=13, color=DARK_BLUE)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — NOTES SLIDE 3c: Validation concept
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Internal Validation: Checking Which Path Is More Accurate",
       "Using the ERA5 100 m wind as a check on the 10 m power-law extrapolation")

bullets(s,
    ["ERA5 provides both 10 m and 100 m wind speeds directly — this gives an opportunity for a check",
     "The idea: if we apply the same power-law formula to extrapolate only from 10 m up to 100 m, "
     "we can compare that result against the actual ERA5 100 m wind",
     "If the 10 m power-law overestimates the actual 100 m wind, it is likely also overestimating at 150 m"],
    0.4, 1.45, 9.2, 2.4, title="The validation idea", size=14, tsize=15, spacing=5)

rect(s, 0.4, 3.95, 9.2, 0.04, fill=ORANGE)

# visual flow
for i, (lbl, clr) in enumerate([
    ("ERA5 10 m wind", MID_BLUE),
    ("Power-law → 100 m", ORANGE),
    ("Compare vs ERA5 actual 100 m", GREEN),
]):
    x = 0.55 + i * 3.1
    rect(s, x, 4.1, 2.7, 0.72, fill=LIGHT_BLUE if i < 2 else PALE_GREEN,
         line=MID_BLUE if i < 2 else GREEN)
    text(s, lbl, x+0.08, 4.22, 2.55, 0.5, size=13, bold=True,
         color=clr, align=PP_ALIGN.CENTER)
    if i < 2:
        text(s, "→", x+2.72, 4.32, 0.35, 0.4, size=18, bold=True, color=DARK_BLUE)

text(s,
    "This gives a direct, data-based check on how well α = 0.11 represents "
    "the real vertical wind shear in this ERA5 region.",
    0.4, 5.0, 9.2, 0.6, size=13, color=DARK_BLUE)

bullets(s,
    ["If bias is small → the 10 m power-law is trustworthy at 150 m too",
     "If bias is positive (overpredict) → the 10 m based 150 m estimate is likely too high as well"],
    0.4, 5.7, 9.2, 1.35, title="What to conclude", size=13, tsize=14, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — NOTES SLIDE 3d: Validation result
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Validation Result: 10 m → 100 m vs Actual ERA5 100 m",
       "With α = 0.11, the 10 m power-law extrapolation is biased high at 100 m")

img(s, "fig_monthly_mean_ws100_validation.png", 0.3, 1.42, w=9.4)

stat(s, "Actual ERA5\n100 m mean", "10.04 m/s", 0.3, 5.42, w=2.2, h=0.92)
stat(s, "10 m extrap.\nto 100 m mean", "10.75 m/s", 2.6, 5.42, w=2.2, h=0.92,
     bg_c=CREAM, border=ORANGE, vcolor=ORANGE)
stat(s, "Bias", "+0.71 m/s", 4.9, 5.42, w=2.2, h=0.92,
     bg_c=CREAM, border=ORANGE, vcolor=ORANGE)
stat(s, "MAE", "0.84 m/s", 7.2, 5.42, w=2.2, h=0.92,
     bg_c=CREAM, border=ORANGE, vcolor=ORANGE)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — NOTES SLIDE 3e: Validation interpretation
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "What the Validation Tells Us",
       "Interpreting the bias for the 150 m extrapolation")

rect(s, 0.4, 1.45, 9.2, 2.35, fill=CREAM, line=ORANGE)
text(s, "Key finding",
     0.6, 1.52, 2.0, 0.38, size=14, bold=True, color=ORANGE)
text(s,
    "With α = 0.11, the 10 m power-law already overpredicts the actual ERA5 100 m wind "
    "by +0.71 m/s on average (MAPE = 9.76%). "
    "Since the 10 m method is biased high at 100 m, it is plausible that it is also biased high at 150 m.",
    0.6, 1.95, 8.85, 1.6, size=14, color=BLACK)

bullets(s,
    ["Path A (10 m) remains the paper-consistent baseline — it is what Chai et al. 2024 uses",
     "Path B (100 m) is the more trustworthy sensitivity estimate — it starts closer to hub height and depends less on the assumed α",
     "The 100 m based 150 m extrapolation is a shorter, more robust step: factor of 1.5 vs factor of 15"],
    0.4, 3.95, 9.2, 2.1, title="What this means for this analysis", size=14, tsize=15, spacing=5)

rect(s, 0.4, 6.12, 9.2, 0.04, fill=MID_BLUE)
text(s,
    "Both paths are kept: Path A for paper replication, Path B as a built-in sensitivity check.",
    0.4, 6.22, 9.2, 0.45, size=13, bold=True, color=DARK_BLUE, align=PP_ALIGN.CENTER)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — NOTES SLIDE 4a: Alpha sensitivity plot
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Sensitivity of Hub-Height Wind to the Shear Exponent α",
       "How much does the extrapolated wind change when α changes?")

img(s, "fig_alpha_sensitivity.png", 0.3, 1.42, w=9.4)

bullets(s,
    ["The x-axis shows different values of α tested; the y-axis shows the resulting mean hub-height wind",
     "Blue line (Path A, from 10 m): rises steeply as α increases — very sensitive to the shear assumption",
     "Orange line (Path B, from 100 m): nearly flat — barely changes with α",
     "This is expected: a larger height jump amplifies any error in α much more strongly"],
    0.3, 5.45, 9.4, 1.82, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — NOTES SLIDE 4b: Alpha sensitivity table
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Alpha Sensitivity — Numbers",
       "Mean hub-height 10-min wind (m/s) at different α values")

# table
col_x = [1.0, 3.6, 6.2]
col_w = [2.5, 2.5, 2.5]
rh = 0.5

def trow(s, vals, top, bg_c, bold=False, color=BLACK):
    for v, x, w in zip(vals, col_x, col_w):
        rect(s, x, top, w-0.05, rh, fill=bg_c, line=RGBColor(0xCC,0xCC,0xCC))
        text(s, v, x+0.08, top+0.09, w-0.18, rh-0.12, size=13, bold=bold,
             color=color, align=PP_ALIGN.CENTER)

trow(s, ["α", "Mean V_hub from 10 m (m/s)", "Mean V_hub from 100 m (m/s)"],
     1.45, DARK_BLUE, bold=True, color=WHITE)
rows = [
    ("0.08", "11.40", "11.41"),
    ("0.10", "12.04", "11.51"),
    ("0.11  ← paper value", "12.37", "11.55"),
    ("0.14", "13.42", "11.69"),
    ("0.20", "15.78", "11.98"),
]
for i, row in enumerate(rows):
    bg_c = LIGHT_BLUE if i % 2 == 0 else WHITE
    bold = (i == 2)
    clr  = MID_BLUE if bold else BLACK
    trow(s, row, 1.95 + i*rh, bg_c, bold=bold, color=clr)

rect(s, 0.4, 4.68, 9.2, 0.04, fill=MID_BLUE)
bullets(s,
    ["Going from α = 0.11 to α = 0.20 (nearly double), Path A rises by +3.4 m/s (27% increase)",
     "Over the same range, Path B rises by only +0.4 m/s (3.8% increase)",
     "This confirms that any uncertainty in α has a much larger impact on the 10 m based estimate",
     "The 100 m based path is inherently more robust to shear-model assumptions"],
    0.4, 4.78, 9.2, 2.3, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — Annual maxima (block-maxima sample)
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Annual Maxima of Hub-Height Wind",
       "The block-maxima sample used in Gumbel and GEV fitting")

img(s, "fig_annual_maxima_compare.png", 0.3, 1.42, w=9.4)

bullets(s,
    ["Each point is the single highest hub-height wind recorded in that calendar year",
     "These annual maxima are the inputs for the Gumbel and GEV extreme-value fits",
     "The two paths track each other — Path B (100 m) tends to give slightly higher annual maxima",
     "26 data points in total (1950–1975 subset) — enough to fit, but uncertainty in long return levels is still large",
     "A longer ERA5 record will reduce this uncertainty significantly"],
    0.3, 5.42, 9.4, 1.9, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — Five EVA methods: what they are
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Five Extreme-Value Methods",
       "Tested to quantify model-form uncertainty — not to pick just one")

method_data = [
    ("Gumbel", "Block maxima", "F(x) = exp(−exp(−(x−μ)/β))",
     "Fit to annual maxima. Simple and conservative. Used directly in Chai et al. 2024."),
    ("GEV", "Block maxima", "F(x) = exp(−(1 + ξ(x−μ)/σ)^(−1/ξ))",
     "More flexible than Gumbel — allows heavy or light tails via shape parameter ξ."),
    ("POT / GPD", "Peaks over threshold", "P(Y≤y) = 1 − (1 + ξy/σ_u)^(−1/ξ)",
     "Uses all peaks above a threshold, not just one maximum per year. More data-efficient."),
    ("Weibull", "Block maxima", "F(x) = 1 − exp(−(x/λ)^k)",
     "Common engineering benchmark for positive wind and load variables."),
    ("Lognormal", "Block maxima", "F(x) = Φ(( ln x − μ) / σ)",
     "Benchmark for positive right-skewed variables."),
]
for i, (name, mtype, eq, desc) in enumerate(method_data):
    t = 1.42 + i * 1.02
    rect(s, 0.3, t, 9.4, 0.96, fill=LIGHT_BLUE if i%2==0 else WHITE, line=MID_BLUE)
    text(s, name, 0.45, t+0.06, 1.6, 0.3, size=13, bold=True, color=DARK_BLUE)
    text(s, mtype, 2.12, t+0.06, 1.6, 0.3, size=11, color=GREY_TEXT)
    text(s, eq, 3.85, t+0.06, 5.7, 0.32, size=11, bold=True, color=MID_BLUE)
    text(s, desc, 0.45, t+0.46, 9.15, 0.38, size=11, color=BLACK)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — MRL plot: POT threshold diagnostic
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Choosing the POT Threshold — Mean Residual Life Plot",
       "Justifying the threshold used in the GPD/POT extreme-value fit")

img(s, "fig_pot_mrl.png", 0.3, 1.42, w=6.0)

bullets(s,
    ["The POT method fits a distribution only to values above a chosen threshold u",
     "The threshold must be high enough to be in the tail, but not so high that too few data points remain",
     "The Mean Residual Life (MRL) plot is the standard diagnostic for this choice"],
    6.5, 1.55, 3.2, 2.0, size=12, title="What is MRL?", tsize=13, spacing=4)

rect(s, 6.5, 3.65, 3.2, 0.04, fill=MID_BLUE)
bullets(s,
    ["If the line is approximately straight over a range of thresholds, a GPD tail model is appropriate there",
     "Threshold chosen: q = 0.95  →  u = 21.8 m/s",
     "602 declustered peaks used in the final GPD fit"],
    6.5, 3.75, 3.2, 2.4, size=12, title="Reading this plot", tsize=13, spacing=4)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — Return-level bar chart
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Return-Level Estimates Across Five Methods",
       "Area-mean V_hub (10-min equivalent), ERA5 1950–1975 subset")

img(s, "fig_return_levels.png", 0.3, 1.42, w=9.4)

bullets(s,
    ["Each bar group shows the 50-year and 100-year return levels for one method",
     "Gumbel stands clearly above the rest — it is the most conservative estimate by ~3 m/s",
     "The other four methods cluster between 32–34 m/s for the 100-year return level",
     "The spread between methods is the model-form uncertainty — how much the answer depends on which model you chose"],
    0.3, 5.58, 9.4, 1.72, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — Return-level results table
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Return-Level Results — Full Table (10 m Baseline)",
       "Path A (from 10 m), α = 0.11, ERA5 1950–1975 subset")

col_x = [0.3,  3.2,  5.6,  7.9]
col_w = [2.85, 2.3,  2.25, 1.95]
rh = 0.5

def tr(s, vals, top, bg_c, bold=False, color=BLACK):
    for v, x, w in zip(vals, col_x, col_w):
        rect(s, x, top, w-0.05, rh, fill=bg_c, line=RGBColor(0xCC,0xCC,0xCC))
        text(s, v, x+0.08, top+0.09, w-0.18, rh-0.12, size=13, bold=bold,
             color=color, align=PP_ALIGN.LEFT)

tr(s, ["Method", "50-yr return level", "100-yr return level", "Notes"],
   1.45, DARK_BLUE, bold=True, color=WHITE)
rows_t = [
    ("Gumbel",    "35.30 m/s", "36.31 m/s", "Most conservative"),
    ("GEV",       "32.74 m/s", "32.90 m/s", "Flexible EVT"),
    ("Weibull",   "32.67 m/s", "32.88 m/s", "Engineering benchmark"),
    ("Lognormal", "33.27 m/s", "33.68 m/s", "Skewed benchmark"),
    ("POT / GPD", "32.91 m/s", "33.16 m/s", "Threshold-based EVT"),
]
for i, row in enumerate(rows_t):
    bg_c = LIGHT_BLUE if i%2==0 else WHITE
    is_g = (i == 0)
    tr(s, row, 1.95+i*rh, bg_c, bold=is_g, color=ORANGE if is_g else BLACK)

rect(s, 0.3, 4.62, 9.4, 0.04, fill=MID_BLUE)

bullets(s,
    ["Gumbel 100-yr result (36.31 m/s) is ~3.1 m/s higher than the next highest method — it uses only annual maxima, losing information from the rest of the data",
     "GEV, Weibull, Lognormal and POT/GPD all agree within ~0.8 m/s of each other — consistent cluster",
     "The spread of ~3.4 m/s between Gumbel and the cluster is the model-form uncertainty on this dataset",
     "These are preliminary values from a 25.5-year subset — uncertainty will decrease with longer records"],
    0.3, 4.72, 9.4, 2.42, size=13, spacing=3)

footer(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 17 — Next steps
# ══════════════════════════════════════════════════════════════════════════════
s = slide(prs); bg(s, WHITE)
header(s, "Next Steps",
       "What this preliminary ERA5 workflow feeds into")

left = [
    "Complete the ERA5 download to the full target period",
    "Build Hs and Tp time series from the wave data stream (already downloaded)",
    "Fit the joint wind-wave environmental model: f(Uw) · f(Hs|Uw) · f(Tp|Hs, Uw)",
    "Generate 100-year environmental contours using IFORM",
    "Select environmental condition points and compare against Chai et al. 2024",
]
right = [
    "Set up OpenFAST batch runs for selected environmental conditions",
    "Extract structural response channels: mooring tensions, tower base moments",
    "Apply Gumbel and ACER extreme estimation to response peaks",
    "Split ERA5 into moving windows → track nonstationary return levels over time",
    "Quantify how environmental and structural extremes shift across the ERA5 record",
]

rect(s, 0.3, 1.45, 4.55, 0.38, fill=MID_BLUE)
text(s, "Phase 1–3: Environmental Inputs & Contours",
     0.4, 1.49, 4.35, 0.3, size=12, bold=True, color=WHITE)
bullets(s, left, 0.3, 1.87, 4.55, 3.1, size=12, spacing=3)

rect(s, 5.1, 1.45, 4.55, 0.38, fill=DARK_BLUE)
text(s, "Phase 4–6: Loads, ACER & Climate Trends",
     5.2, 1.49, 4.35, 0.3, size=12, bold=True, color=WHITE)
bullets(s, right, 5.1, 1.87, 4.55, 3.1, size=12, spacing=3)

rect(s, 0.3, 5.1, 9.4, 0.04, fill=ORANGE)
text(s,
    "This preliminary analysis demonstrates the ERA5 pipeline is working. "
    "The next stage connects it to the paper's contour-based environmental model and OpenFAST structural response runs.",
    0.3, 5.22, 9.4, 0.85, size=13, color=DARK_BLUE)

footer(s)


# ── Save ──────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "meeting_slides.pptx")
prs.save(out)
print(f"Saved: {out}  ({prs.slides.__len__()} slides)")
