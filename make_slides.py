"""
Generate meeting slides for PhD supervisor meeting.
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
BLUE_LIGHT_TEXT = RGBColor(0xBB, 0xCC, 0xDD)


# ── helpers ──────────────────────────────────────────────────────────────────

def add_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color=None, line_color=None):
    shape = slide.shapes.add_shape(
        1, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, text, left, top, width, height,
                font_size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    return tb


def add_bullets(slide, items, left, top, width, height,
                font_size=14, title=None, title_size=15,
                color=BLACK, title_color=MID_BLUE):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    if title:
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = title
        r.font.size = Pt(title_size)
        r.font.bold = True
        r.font.color.rgb = title_color
        first = False
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run()
        r.text = "• " + item
        r.font.size = Pt(font_size)
        r.font.color.rgb = color
    return tb


def add_header(slide, title, subtitle=None):
    add_rect(slide, 0, 0, 10, 1.35, fill_color=DARK_BLUE)
    add_textbox(slide, title, 0.25, 0.1, 9.5, 0.72,
                font_size=26, bold=True, color=WHITE)
    if subtitle:
        add_textbox(slide, subtitle, 0.25, 0.78, 9.5, 0.45,
                    font_size=13, color=BLUE_LIGHT_TEXT)


def add_footer(slide, text="PhD Supervisor Meeting  |  March 2026"):
    add_textbox(slide, text, 0, 7.3, 10, 0.35,
                font_size=9, color=GREY_TEXT, align=PP_ALIGN.CENTER)


def add_image(slide, path, left, top, width=None, height=None):
    if not os.path.exists(path):
        return
    kw = {}
    if width:
        kw["width"] = Inches(width)
    if height:
        kw["height"] = Inches(height)
    slide.shapes.add_picture(path, Inches(left), Inches(top), **kw)


def table_row(slide, cols, col_x, col_w, top, row_h, bg, text_color=BLACK,
              bold=False, font_size=12, header=False):
    for val, x, w in zip(cols, col_x, col_w):
        add_rect(slide, x, top, w - 0.04, row_h,
                 fill_color=bg, line_color=RGBColor(0xCC, 0xCC, 0xCC))
        add_textbox(slide, val, x + 0.07, top + 0.07, w - 0.15, row_h - 0.1,
                    font_size=font_size, bold=bold, color=text_color,
                    align=PP_ALIGN.CENTER if header else PP_ALIGN.LEFT)


# ── build ─────────────────────────────────────────────────────────────────────

prs = Presentation()
prs.slide_width  = Inches(10)
prs.slide_height = Inches(7.5)


# ═══ TITLE ════════════════════════════════════════════════════════════════════
s = add_slide(prs)
add_rect(s, 0, 0, 10, 7.5, fill_color=DARK_BLUE)
add_rect(s, 0, 2.75, 10, 2.25, fill_color=MID_BLUE)

add_textbox(s, "ERA5-Based Extreme Wind & Wave Analysis",
            0.5, 0.9, 9.0, 1.05, font_size=33, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER)
add_textbox(s, "Preliminary Pipeline: Hub-Height Extrapolation, Sensitivity Analysis\n& Extreme-Value Methods",
            0.5, 2.0, 9.0, 0.65, font_size=16, color=BLUE_LIGHT_TEXT,
            align=PP_ALIGN.CENTER)
add_textbox(s, "PhD Supervisor Meeting  ·  March 2026",
            0.5, 2.88, 9.0, 0.45, font_size=15, color=WHITE, align=PP_ALIGN.CENTER)
add_textbox(s, "Data: ERA5 reanalysis (1950–1975 subset)  ·  Target: IEA 15 MW, Northern North Sea",
            0.5, 3.45, 9.0, 0.55, font_size=13, color=RGBColor(0xCC, 0xDD, 0xEE),
            align=PP_ALIGN.CENTER)
add_textbox(s, "Preliminary results — incomplete ERA5 subset, not final thesis values",
            0.5, 6.85, 9.0, 0.4, font_size=11, color=ORANGE, align=PP_ALIGN.CENTER)


# ═══ SLIDE 1: Objective & Status ══════════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Objective & Current Status",
           "Replication target + ERA5 wind-and-wave pipeline")

add_bullets(s,
    ["Replication target: Chai et al. (2024) — short-term extreme structural responses for the IEA 15 MW turbine under extreme environmental conditions",
     "In parallel: building an ERA5 climate-data pipeline to replace stationary environmental conditions with time-evolving ERA5 statistics",
     "Goal: quantify how environmental extremes (and downstream structural extremes) shift across the ERA5 record"],
    0.4, 1.5, 9.2, 1.95, title="Why this work?", font_size=14)

add_rect(s, 0.4, 3.52, 9.2, 0.04, fill_color=MID_BLUE)

add_bullets(s,
    ["ERA5 subset processed: 1950-01-01 → 1975-06-30  (~25.5 years, 306 monthly files)",
     "Wind variables: u10, v10, u100, v100  (all levels available)",
     "Wave variables: Hs (significant wave height), Tp (peak period) — confirmed present in downloaded files",
     "ERA5 files are ZIP containers with two inner NetCDFs; reader updated to merge both streams",
     "Today's demo: dual-path hub-height extrapolation + five extreme-value methods on real ERA5 data"],
    0.4, 3.65, 9.2, 2.7, title="Current status", font_size=14)

add_footer(s)


# ═══ SLIDE 2: Data structure discovery ════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Wave Data Was Already Downloaded",
           "The issue was in the reader, not the downloader")

# left: what was found
add_rect(s, 0.3, 1.5, 4.3, 4.1, fill_color=LIGHT_BLUE, line_color=MID_BLUE)
add_textbox(s, "File structure discovered", 0.45, 1.58, 4.0, 0.38,
            font_size=14, bold=True, color=DARK_BLUE)
add_textbox(s,
    "era5_sl_YYYY_MM.nc  (ZIP container)\n"
    "  ├─ data_stream-oper_stepType-instant.nc\n"
    "  │     u10, v10, u100, v100\n"
    "  └─ data_stream-wave_stepType-instant.nc\n"
    "        Hs (swh),  Tp (pp1d)",
    0.45, 2.05, 4.05, 1.9, font_size=13, color=DARK_BLUE)

add_textbox(s, "download_era5.py was always requesting:",
            0.45, 4.05, 4.0, 0.32, font_size=12, bold=True, color=BLACK)
add_bullets(s,
    ["significant_height_of_combined_wind_waves_and_swell",
     "peak_wave_period"],
    0.45, 4.4, 4.05, 0.95, font_size=12)

# right: what to do
add_rect(s, 4.85, 1.5, 4.85, 4.1, fill_color=RGBColor(0xFF, 0xF4, 0xEA), line_color=ORANGE)
add_textbox(s, "Fix applied to analysis scripts", 4.98, 1.58, 4.6, 0.38,
            font_size=14, bold=True, color=ORANGE)
add_bullets(s,
    ["quick_demo_extremes.py: now opens both inner NetCDFs and merges wind + wave streams",
     "compare_extreme_methods.py: updated to ingest the merged dataset",
     "Wave variables (Hs, Tp) available for joint model as soon as full ERA5 period is downloaded",
     "No re-downloading needed — data was already correct"],
    4.98, 2.05, 4.6, 2.9, font_size=13)

add_textbox(s, "Next: use Hs and Tp to build the joint wind-wave environmental model",
            0.4, 5.75, 9.2, 0.45, font_size=13, bold=True, color=MID_BLUE,
            align=PP_ALIGN.CENTER)

add_footer(s)


# ═══ SLIDE 3: Hub-height conversion (dual path) ═══════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Hub-Height Conversion — Two Paths",
           "Paper-consistent baseline (10 m) vs. ERA5 sensitivity check (100 m)")

# path 1 box
add_rect(s, 0.3, 1.5, 4.4, 2.55, fill_color=LIGHT_BLUE, line_color=MID_BLUE)
add_textbox(s, "Path A — from 10 m  (paper baseline)", 0.45, 1.57, 4.1, 0.38,
            font_size=13, bold=True, color=DARK_BLUE)
add_textbox(s,
    "U_hub,10(1h) = U₁₀ × (150/10)^α\nV_hub(10min) = 1.10 × U_hub,10(1h)",
    0.45, 2.02, 4.1, 0.75, font_size=14, bold=True, color=DARK_BLUE)
add_bullets(s,
    ["α = 0.11 (IEC power-law, Chai et al. 2024)",
     "10 m is the environmental wind reference height in the paper",
     "Large vertical extrapolation: 10 m → 150 m"],
    0.45, 2.82, 4.1, 1.1, font_size=12)

# path 2 box
add_rect(s, 5.0, 1.5, 4.4, 2.55, fill_color=RGBColor(0xFF, 0xF4, 0xEA), line_color=ORANGE)
add_textbox(s, "Path B — from 100 m  (sensitivity check)", 5.15, 1.57, 4.1, 0.38,
            font_size=13, bold=True, color=ORANGE)
add_textbox(s,
    "U_hub,100(1h) = U₁₀₀ × (150/100)^α\nV_hub(10min) = 1.10 × U_hub,100(1h)",
    5.15, 2.02, 4.1, 0.75, font_size=14, bold=True, color=ORANGE)
add_bullets(s,
    ["Same α = 0.11; ERA5 provides 100 m wind directly",
     "Shorter extrapolation: 100 m → 150 m",
     "Sensitivity check on vertical shear assumption"],
    5.15, 2.82, 4.1, 1.1, font_size=12)

# gap summary box
add_rect(s, 0.3, 4.2, 9.1, 1.5, fill_color=RGBColor(0xF0, 0xF5, 0xFF), line_color=DARK_BLUE)
add_textbox(s, "Observed gap between the two paths (area-mean V_hub, 1950–1975 subset)",
            0.45, 4.28, 8.8, 0.35, font_size=13, bold=True, color=DARK_BLUE)

gap_cols  = ["Mean |Δ| (m/s)", "Median |Δ| (m/s)", "Max |Δ| (m/s)", "Mean |Δ| (%)"]
gap_vals  = ["0.960",          "0.969",             "2.612",          "8.66%"]
gx = [0.4, 2.7, 5.0, 7.3]
gw = 2.2
for col, val, x in zip(gap_cols, gap_vals, gx):
    add_textbox(s, col, x, 4.7, gw, 0.3, font_size=11, color=GREY_TEXT, align=PP_ALIGN.CENTER)
    add_textbox(s, val, x, 5.02, gw, 0.45, font_size=17, bold=True, color=DARK_BLUE,
                align=PP_ALIGN.CENTER)

add_bullets(s,
    ["Gap is non-negligible (~9% mean) — choice of source height affects extrapolated return levels",
     "Path A (10 m) is used as the primary analysis to match the paper; Path B shown as sensitivity"],
    0.3, 5.85, 9.1, 1.0, font_size=13)

add_footer(s)


# ═══ SLIDE 4: Time series (comparison) ════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Hub-Height Wind Time Series — Both Extrapolation Paths",
           "Area-mean V_hub (10-min), monthly maxima and annual maxima")

add_image(s, os.path.join(DEMO_OUT, "fig_timeseries_vhub_compare.png"), 0.25, 1.45, width=9.5)

add_bullets(s,
    ["Two paths track each other closely through time — divergence visible in high-wind months",
     "Annual block-maxima (next figure) show 100 m path gives slightly higher annual maxima on average",
     "No obvious trend or discontinuity in this subset — block-maxima modeling is feasible",
     "26 annual maxima → Gumbel/GEV estimates carry substantial uncertainty; longer record needed"],
    0.3, 5.55, 9.4, 1.7, font_size=13)

add_footer(s)


# ═══ SLIDE 5: Annual maxima + gap ═════════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Annual Maxima & Extrapolation Gap",
           "Block-maxima inputs and sensitivity of hub-height wind to source level")

add_image(s, os.path.join(DEMO_OUT, "fig_annual_maxima_compare.png"), 0.25, 1.45, width=4.8)
add_image(s, os.path.join(DEMO_OUT, "fig_extrapolation_gap.png"),     5.1,  1.45, width=4.8)

add_bullets(s,
    ["Left: 100 m based path tends to give slightly higher annual maxima — consistent with smaller relative shear correction",
     "Right: monthly mean gap between the two paths; mostly positive (10 m path gives lower V_hub) with seasonal structure",
     "Seasonal structure in the gap implies the shear assumption is not neutral year-round",
     "This motivates eventually using a dynamic α from the u10/u100 pair rather than a fixed α = 0.11"],
    0.25, 5.6, 9.5, 1.7, font_size=13)

add_footer(s)


# ═══ SLIDE 6: Five extreme-value methods ══════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Five Extreme-Value Methods",
           "Quantifying model-form uncertainty before committing to one approach")

method_cards = [
    ("Gumbel (block maxima)",    "Classical EVT; simple; used directly in Chai et al. 2024"),
    ("GEV (block maxima)",       "More flexible than Gumbel — shape parameter ξ free"),
    ("POT / GPD",                "Threshold-based EVT; uses more data than annual maxima alone"),
    ("Weibull (block maxima)",   "Common engineering benchmark for positive wind/load variables"),
    ("Lognormal (block maxima)", "Benchmark for positive-skewed variables"),
]
for i, (name, desc) in enumerate(method_cards):
    top = 1.5 + i * 0.77
    add_rect(s, 0.25, top, 3.8, 0.66, fill_color=LIGHT_BLUE, line_color=MID_BLUE)
    add_textbox(s, name, 0.38, top + 0.04, 3.55, 0.28, font_size=12, bold=True, color=DARK_BLUE)
    add_textbox(s, desc, 0.38, top + 0.32, 3.55, 0.3,  font_size=11, color=BLACK)

add_image(s, os.path.join(DEMO_OUT, "fig_pot_mrl.png"), 4.25, 1.45, width=5.5)
add_bullets(s,
    ["Mean residual life plot: near-linear mean excess above threshold → GPD tail is appropriate",
     "Threshold: q = 0.95 → 21.8 m/s;  602 declustered peaks used in GPD fit"],
    4.25, 6.08, 5.5, 1.05, font_size=12)

add_footer(s)


# ═══ SLIDE 7: Results table ════════════════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Return-Level Estimates — Both Paths, Five Methods",
           "Area-mean V_hub (10-min), ERA5 1950–1975 subset")

# table: 5 methods × 4 columns (method, 50y 10m, 100y 10m, 100y 100m)
methods  = ["Gumbel",    "GEV",    "Weibull", "Lognormal", "POT / GPD"]
rl50_10  = [35.30,       32.74,    32.67,     33.27,       32.91]
rl100_10 = [36.31,       32.90,    32.88,     33.68,       33.16]
rl100_100= [36.68,       33.31,    33.22,     34.17,       34.40]   # from user context

col_x = [0.3,  3.1,  5.4,  7.7]
col_w = [2.75, 2.2,  2.2,  2.1]
row_h = 0.46

# header row
table_row(s, ["Method", "50-yr RL 10m (m/s)", "100-yr RL 10m (m/s)", "100-yr RL 100m (m/s)"],
          col_x, col_w, 1.5, row_h, DARK_BLUE, WHITE, bold=True, font_size=12, header=True)

for i, (m, r50, r100_10, r100_100) in enumerate(zip(methods, rl50_10, rl100_10, rl100_100)):
    top = 1.96 + i * row_h
    bg  = LIGHT_BLUE if i % 2 == 0 else WHITE
    is_gumbel = (m == "Gumbel")
    clr = ORANGE if is_gumbel else BLACK
    table_row(s, [m, f"{r50:.2f}", f"{r100_10:.2f}", f"{r100_100:.2f}"],
              col_x, col_w, top, row_h, bg, clr, bold=is_gumbel, font_size=12)

add_image(s, os.path.join(DEMO_OUT, "fig_return_levels.png"), 0.3, 4.26, width=4.5)

add_bullets(s,
    ["Gumbel is most conservative (~36.3 m/s from 10m, ~36.7 m/s from 100m)",
     "All other methods cluster near 33–34 m/s — spread quantifies model-form uncertainty",
     "100 m path gives consistently higher return levels than 10 m path (~0.4–1.2 m/s at 100 yr)",
     "Paper uses Gumbel + ACER; Gumbel is conservative and transparent for maxima-based extrapolation"],
    4.95, 4.26, 4.85, 2.85, title="Key takeaway", font_size=13)

add_rect(s, 0.3, 7.05, 9.4, 0.04, fill_color=ORANGE)
add_textbox(s, "Preliminary values from a 25.5-year subset — not final thesis results",
            0.3, 7.1, 9.4, 0.32, font_size=11, bold=True, color=ORANGE,
            align=PP_ALIGN.CENTER)

add_footer(s)


# ═══ SLIDE 8: Next steps ══════════════════════════════════════════════════════
s = add_slide(prs)
set_bg(s, WHITE)
add_header(s, "Next Steps",
           "Connecting ERA5 pipeline to paper replication and climate-change analysis")

left_items = [
    "Complete ERA5 download to full target period",
    "Build Hs and Tp time series from the now-readable wave stream",
    "Fit joint environmental model: f(Uw) · f(Hs|Uw) · f(Tp|Hs, Uw)",
    "Generate 100-year IFORM contours + EC selection points",
    "Compare contour shapes/magnitudes against Chai et al. 2024",
]
right_items = [
    "Set up OpenFAST batch runs for selected environmental conditions",
    "Extract response channels: mooring tensions, TwrBsFyt, TwrBsMxt",
    "Reproduce Gumbel and ACER extreme estimation on response peaks",
    "Split ERA5 into moving windows → nonstationary return-level trends",
    "Quantify change in environmental and structural extremes over ERA5 record",
]

add_rect(s, 0.3, 1.5, 4.55, 0.38, fill_color=MID_BLUE)
add_textbox(s, "Phase 1–3: Data & Environmental Contours",
            0.4, 1.54, 4.35, 0.3, font_size=12, bold=True, color=WHITE)
add_bullets(s, left_items, 0.3, 1.92, 4.55, 3.0, font_size=12)

add_rect(s, 5.1, 1.5, 4.55, 0.38, fill_color=DARK_BLUE)
add_textbox(s, "Phase 4–6: OpenFAST, ACER & Climate Trends",
            5.2, 1.54, 4.35, 0.3, font_size=12, bold=True, color=WHITE)
add_bullets(s, right_items, 5.1, 1.92, 4.55, 3.0, font_size=12)

add_rect(s, 0.3, 5.08, 9.4, 0.04, fill_color=ORANGE)
add_bullets(s,
    ["Should the primary study area stay strictly northern North Sea before extending to Ireland/Atlantic?",
     "First full replication: preserve paper assumptions exactly, then add sensitivity — or include sensitivity immediately?",
     "Dynamic α (from u10/u100 pair) as standard baseline, or as a later sensitivity test only?"],
    0.3, 5.18, 9.4, 2.05,
    title="Questions for supervisor", font_size=13, title_color=ORANGE)

add_footer(s)


# ── Save ─────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "meeting_slides.pptx")
prs.save(out)
print(f"Saved: {out}")
