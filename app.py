"""
Crop Cooling Financial Model — Streamlit UI
Sonoma County Pinot Noir
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ═══════════════════════════════════════════════════════════════════════
# MODEL ENGINE (same logic as main.py, extended for per-day temperatures)
# ═══════════════════════════════════════════════════════════════════════

HEAT_SENSITIVITY = 1.20   # Pinot Noir vs Cab Sauv baseline
COMPOUND_RATE    = 0.10   # 10% daily compounding
OVERNIGHT_LOW    = 65.0   # Default overnight low


def diurnal_temp(hour: float, peak: float, low: float) -> float:
    avg = (peak + low) / 2.0
    amp = (peak - low) / 2.0
    return avg + amp * math.sin(2.0 * math.pi * (hour - 9.0) / 24.0)


def hourly_temps(peak: float, low: float,
                 cooling_delta: float = 0.0,
                 cooling_hours: int = 0) -> list[tuple[int, float]]:
    raw = [(h, diurnal_temp(h, peak, low)) for h in range(24)]
    if cooling_hours > 0 and cooling_delta > 0:
        ranked = sorted(raw, key=lambda x: -x[1])
        cooled_set = {h for h, _ in ranked[:cooling_hours]}
        return [(h, t - cooling_delta if h in cooled_set else t)
                for h, t in raw]
    return raw


def degree_hours(temps: list[tuple[int, float]], threshold: float) -> float:
    return sum(max(0.0, t - threshold) for _, t in temps)


def _saturate(dh: float, ref_dh: float, ref_dmg: float,
              max_dmg: float, sensitivity: float = 1.0) -> float:
    if dh <= 0:
        return 0.0
    if ref_dmg >= max_dmg:
        ref_dmg = max_dmg * 0.95
    k = -math.log(1.0 - ref_dmg / max_dmg) / ref_dh
    return max_dmg * (1.0 - math.exp(-k * sensitivity * dh))


def estimate_damage_multiday(daily_peaks: list[float], overnight_low: float,
                              sensitivity: float,
                              cooling_delta: float = 0.0,
                              cooling_hours: int = 0) -> dict:
    """
    Estimate cumulative damage across a multi-day heatwave with
    different peak temperatures per day.
    """
    total_dh95 = 0.0
    total_dh100 = 0.0

    for day_idx, peak in enumerate(daily_peaks):
        temps = hourly_temps(peak, overnight_low, cooling_delta, cooling_hours)
        day_compound = (1 + COMPOUND_RATE) ** day_idx
        total_dh95  += degree_hours(temps, 95.0) * day_compound
        total_dh100 += degree_hours(temps, 100.0) * day_compound

    # Reference point (Cab Sauv 4-day study at 105°F)
    ref_temps = hourly_temps(105.0, 65.0)
    ref_dh100_day = degree_hours(ref_temps, 100.0)
    ref_dh95_day  = degree_hours(ref_temps, 95.0)
    ref_mult = sum((1 + COMPOUND_RATE) ** d for d in range(4))
    ref_total_dh100 = ref_dh100_day * ref_mult
    ref_total_dh95  = ref_dh95_day  * ref_mult

    s = sensitivity

    sunburn     = _saturate(total_dh100, ref_total_dh100, 0.24, 0.50, s)
    shrivel     = _saturate(total_dh95,  ref_total_dh95,  0.09, 0.20, s)
    anthocyanin = _saturate(total_dh95,  ref_total_dh95,  0.34, 0.65, s)
    acid        = _saturate(total_dh95,  ref_total_dh95,  0.22, 0.55, s)

    yield_loss       = min(0.50, sunburn * 0.35 + shrivel * 0.70)
    quality_discount = min(0.50, anthocyanin * 0.45 + acid * 0.30 + sunburn * 0.08)

    return dict(
        sunburn=sunburn, shrivel=shrivel,
        anthocyanin=anthocyanin, acid=acid,
        yield_loss=yield_loss, quality_discount=quality_discount,
        total_dh95=total_dh95, total_dh100=total_dh100,
    )


def run_full_model(daily_peaks, overnight_low, price_per_ton,
                   yield_per_acre, cooling_delta, cooling_hours,
                   cost_base, cost_materials, acreage):
    """Run the complete model and return all results."""
    uncooled = estimate_damage_multiday(
        daily_peaks, overnight_low, HEAT_SENSITIVITY)
    cooled = estimate_damage_multiday(
        daily_peaks, overnight_low, HEAT_SENSITIVITY,
        cooling_delta, cooling_hours)

    base_rev = price_per_ton * yield_per_acre
    cost_per_acre = cost_base + cost_materials

    uncooled_rev = base_rev * (1 - uncooled['yield_loss']) * (1 - uncooled['quality_discount'])
    cooled_rev   = base_rev * (1 - cooled['yield_loss'])   * (1 - cooled['quality_discount'])

    protected = cooled_rev - uncooled_rev
    net_benefit = protected - cost_per_acre
    roi = protected / cost_per_acre if cost_per_acre > 0 else 0

    yl_u, yl_c = uncooled['yield_loss'], cooled['yield_loss']
    qd_u, qd_c = uncooled['quality_discount'], cooled['quality_discount']
    yield_value   = base_rev * (yl_u - yl_c) * (1 - qd_u)
    quality_value = base_rev * (1 - yl_c) * (qd_u - qd_c)

    return dict(
        base_rev=base_rev, uncooled_rev=uncooled_rev, cooled_rev=cooled_rev,
        protected=protected, cost_per_acre=cost_per_acre,
        net_benefit=net_benefit, roi=roi,
        yield_value=yield_value, quality_value=quality_value,
        uncooled=uncooled, cooled=cooled,
        acreage=acreage,
    )


# ═══════════════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════════════

def build_temp_chart(daily_peaks, overnight_low, cooling_delta, cooling_hours):
    """Multi-day temperature chart: uncooled vs cooled with threshold bands."""
    hours_all = []
    temps_uncooled = []
    temps_cooled = []

    for day_idx, peak in enumerate(daily_peaks):
        uc = hourly_temps(peak, overnight_low)
        co = hourly_temps(peak, overnight_low, cooling_delta, cooling_hours)
        for (h, tu), (_, tc) in zip(uc, co):
            hours_all.append(day_idx * 24 + h)
            temps_uncooled.append(tu)
            temps_cooled.append(tc)

    fig = go.Figure()

    # Threshold bands
    fig.add_hline(y=100, line_dash="dash", line_color="red",
                  annotation_text="100°F — berry necrosis zone",
                  annotation_position="top left",
                  annotation_font_color="red")
    fig.add_hline(y=95, line_dash="dash", line_color="orange",
                  annotation_text="95°F — stress threshold",
                  annotation_position="top left",
                  annotation_font_color="orange")

    # Temperature lines
    fig.add_trace(go.Scatter(
        x=hours_all, y=temps_uncooled, name="Uncooled",
        line=dict(color="#ef4444", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=hours_all, y=temps_cooled, name="With Cooling",
        line=dict(color="#3b82f6", width=2),
    ))

    # Day separators and labels
    for d in range(len(daily_peaks)):
        if d > 0:
            fig.add_vline(x=d * 24, line_dash="dot",
                          line_color="rgba(0,0,0,0.15)")
        fig.add_annotation(
            x=d * 24 + 12, y=max(daily_peaks) + 3,
            text=f"Day {d+1}<br>{daily_peaks[d]:.0f}°F",
            showarrow=False, font=dict(size=11, color="#666"),
        )

    fig.update_layout(
        title=dict(text="Heatwave Temperature Profile: Uncooled vs Cooled",
                   y=0.98, yanchor="top"),
        xaxis_title="Hour",
        yaxis_title="Temperature (°F)",
        height=500,
        margin=dict(t=80, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.08,
                    xanchor="center", x=0.5),
        yaxis=dict(range=[
            min(55, min(temps_cooled) - 5),
            max(temps_uncooled) + 10
        ]),
    )
    return fig


def build_revenue_chart(r):
    """Revenue comparison bar chart."""
    fig = go.Figure()

    categories = ["Baseline<br>(no heatwave)", "After Heatwave<br>(no cooling)",
                   "After Heatwave<br>(with cooling)"]
    values = [r['base_rev'], r['uncooled_rev'], r['cooled_rev']]
    colors = ["#10b981", "#ef4444", "#3b82f6"]

    fig.add_trace(go.Bar(
        x=categories, y=values,
        marker_color=colors,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
    ))

    # Bracket showing revenue protected between bars 2 and 3
    mid_y = (r['uncooled_rev'] + r['cooled_rev']) / 2
    fig.add_shape(
        type="line", x0=1, x1=2, y0=r['uncooled_rev'], y1=r['uncooled_rev'],
        line=dict(color="#16a34a", width=1.5, dash="dot"),
    )
    fig.add_shape(
        type="line", x0=1, x1=2, y0=r['cooled_rev'], y1=r['cooled_rev'],
        line=dict(color="#16a34a", width=1.5, dash="dot"),
    )
    fig.add_annotation(
        x=2, y=mid_y,
        text=f"  <b>${r['protected']:,.0f}</b><br>  protected",
        showarrow=False, font=dict(size=13, color="#000000"),
        xanchor="left",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#16a34a", borderwidth=1, borderpad=4,
    )

    fig.update_layout(
        title="Revenue Per Acre",
        yaxis_title="$/acre",
        height=420,
        margin=dict(t=50, b=40, r=100),
        showlegend=False,
        yaxis=dict(range=[0, r['base_rev'] * 1.2]),
    )
    return fig


def build_damage_chart(r):
    """Horizontal bar chart comparing damage: uncooled vs cooled."""
    categories = ["Sunburn", "Berry Shrivel", "Anthocyanin Loss", "Acid Loss",
                   "Yield Loss", "Quality Discount"]
    uncooled_vals = [
        r['uncooled']['sunburn'], r['uncooled']['shrivel'],
        r['uncooled']['anthocyanin'], r['uncooled']['acid'],
        r['uncooled']['yield_loss'], r['uncooled']['quality_discount'],
    ]
    cooled_vals = [
        r['cooled']['sunburn'], r['cooled']['shrivel'],
        r['cooled']['anthocyanin'], r['cooled']['acid'],
        r['cooled']['yield_loss'], r['cooled']['quality_discount'],
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories, x=[v * 100 for v in uncooled_vals],
        name="No Cooling", orientation="h",
        marker_color="#ef4444",
    ))
    fig.add_trace(go.Bar(
        y=categories, x=[v * 100 for v in cooled_vals],
        name="With Cooling", orientation="h",
        marker_color="#3b82f6",
    ))

    fig.update_layout(
        title="Physiological Damage Comparison",
        xaxis_title="Damage (%)",
        height=420,
        margin=dict(t=80, b=40, l=130),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.06,
                    xanchor="center", x=0.5),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
# STREAMLIT APP
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Crop Cooling Financial Model",
    page_icon=":thermometer:",
    layout="wide",
)

st.title("Crop Cooling Financial Model")
st.markdown("**Sonoma County Pinot Noir** — Research-calibrated heat stress & revenue protection model")

# ─── SIDEBAR INPUTS ──────────────────────────────────────────────────

with st.sidebar:
    st.header("Grape Economics")

    price_per_ton = st.slider(
        "Price per ton ($)",
        min_value=500, max_value=15000, value=3843, step=50,
        help="Sonoma Pinot Noir avg: $3,843 (2023 USDA). Range: $500-$17k.",
    )
    yield_per_acre = st.number_input(
        "Yield (tons/acre)",
        min_value=1.0, max_value=12.0, value=4.0, step=0.5,
        help="UC Davis Russian River Valley: 4.0 tons/acre.",
    )

    st.divider()
    st.header("Heat Event")
    st.caption("Set the peak temperature for each day of the heatwave.")

    col1, col2, col3, col4, col5 = st.columns(5)
    day_temps = [
        col1.number_input("Day 1 °F", min_value=85, max_value=125, value=101),
        col2.number_input("Day 2 °F", min_value=85, max_value=125, value=103),
        col3.number_input("Day 3 °F", min_value=85, max_value=125, value=107),
        col4.number_input("Day 4 °F", min_value=85, max_value=125, value=105),
        col5.number_input("Day 5 °F", min_value=85, max_value=125, value=100),
    ]
    overnight_low = st.number_input(
        "Overnight low (°F)", min_value=45, max_value=85, value=65,
    )

    st.divider()
    st.header("Cooling Technology")

    cooling_delta = st.slider(
        "Cooling effect (°F reduction)",
        min_value=1.0, max_value=8.0, value=4.5, step=0.5,
    )
    cooling_hours = st.select_slider(
        "Cooling hours per day",
        options=list(range(1, 13)), value=4,
    )
    cost_base = st.number_input(
        "Base cost ($/acre)", min_value=0, max_value=2000, value=200, step=10,
    )
    cost_materials = st.number_input(
        "Materials cost ($/acre)", min_value=0, max_value=2000, value=180, step=10,
    )

    st.divider()
    st.header("Scale")

    acreage = st.number_input(
        "Acreage", min_value=1, max_value=10000, value=100, step=10,
    )


# ─── RUN MODEL ───────────────────────────────────────────────────────

r = run_full_model(
    daily_peaks=day_temps,
    overnight_low=overnight_low,
    price_per_ton=price_per_ton,
    yield_per_acre=yield_per_acre,
    cooling_delta=cooling_delta,
    cooling_hours=cooling_hours,
    cost_base=cost_base,
    cost_materials=cost_materials,
    acreage=acreage,
)


# ─── HEADLINE METRICS ────────────────────────────────────────────────

tons_preserved = yield_per_acre * (r['uncooled']['yield_loss'] - r['cooled']['yield_loss'])

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Net Benefit / Acre",
    f"${r['net_benefit']:,.0f}",
    help="Revenue protected minus technology cost, per acre.",
)
m2.metric(
    "ROI",
    f"{r['roi']:.1f}x",
    help="Revenue protected divided by technology cost.",
)
m3.metric(
    "Tons Preserved / Acre",
    f"{tons_preserved:.2f}",
    help=f"Yield saved: {r['uncooled']['yield_loss']:.1%} loss uncooled vs {r['cooled']['yield_loss']:.1%} cooled.",
)
m4.metric(
    "Total Net Benefit",
    f"${r['net_benefit'] * acreage:,.0f}",
    help=f"Net benefit across all {acreage:,} acres.",
)


# ─── TEMPERATURE CHART ───────────────────────────────────────────────

st.plotly_chart(
    build_temp_chart(day_temps, overnight_low, cooling_delta, cooling_hours),
    width="stretch",
)


# ─── REVENUE & DAMAGE SIDE BY SIDE ──────────────────────────────────

col_rev, col_dmg = st.columns(2)

with col_rev:
    st.plotly_chart(build_revenue_chart(r), width="stretch")

with col_dmg:
    st.plotly_chart(build_damage_chart(r), width="stretch")


# ─── FINANCIAL DETAIL ────────────────────────────────────────────────

st.divider()

det1, det2 = st.columns(2)

with det1:
    st.subheader("Financial Breakdown (per acre)")

    base_loss = r['base_rev'] - r['uncooled_rev']
    cooled_loss = r['base_rev'] - r['cooled_rev']

    st.markdown(f"""
    | | |
    |:---|---:|
    | Baseline revenue (no heatwave) | **${r['base_rev']:,.0f}** |
    | After heatwave, no cooling | ${r['uncooled_rev']:,.0f} *(−${base_loss:,.0f})* |
    | After heatwave, with cooling | ${r['cooled_rev']:,.0f} *(−${cooled_loss:,.0f})* |
    | | |
    | **Revenue protected** | **${r['protected']:,.0f}** |
    | &emsp; From yield preservation | ${r['yield_value']:,.0f} ({r['yield_value'] / r['protected'] * 100 if r['protected'] else 0:.0f}%) |
    | &emsp; From quality preservation | ${r['quality_value']:,.0f} ({r['quality_value'] / r['protected'] * 100 if r['protected'] else 0:.0f}%) |
    | Technology cost | (${r['cost_per_acre']:,.0f}) |
    | **Net benefit** | **${r['net_benefit']:,.0f}** |
    """)

with det2:
    st.subheader("Degree-Hours Analysis")

    # Compute per-day DH for display
    total_dh95_uc = 0.0
    total_dh100_uc = 0.0
    total_dh95_co = 0.0
    total_dh100_co = 0.0
    for day_idx, peak in enumerate(day_temps):
        uc = hourly_temps(peak, overnight_low)
        co = hourly_temps(peak, overnight_low, cooling_delta, cooling_hours)
        c = (1 + COMPOUND_RATE) ** day_idx
        total_dh95_uc  += degree_hours(uc, 95.0) * c
        total_dh100_uc += degree_hours(uc, 100.0) * c
        total_dh95_co  += degree_hours(co, 95.0) * c
        total_dh100_co += degree_hours(co, 100.0) * c

    red95  = (1 - total_dh95_co / total_dh95_uc) * 100 if total_dh95_uc else 0
    red100 = (1 - total_dh100_co / total_dh100_uc) * 100 if total_dh100_uc else 0

    st.markdown(f"""
    Cumulative degree-hours across the {len(day_temps)}-day heatwave (with compounding):

    | Threshold | Uncooled | Cooled | Reduction |
    |:----------|--------:|-------:|----------:|
    | Above 95°F | {total_dh95_uc:.1f} DH | {total_dh95_co:.1f} DH | **{red95:.0f}%** |
    | Above 100°F | {total_dh100_uc:.1f} DH | {total_dh100_co:.1f} DH | **{red100:.0f}%** |

    Cooling during the **{cooling_hours} hottest hours** per day eliminates
    **{red100:.0f}%** of degree-hours above the critical 100°F berry-damage
    threshold, where sun-exposed berry surfaces reach the 50°C necrosis zone.
    """)

    st.subheader(f"Scale: {acreage:,} Acres")
    st.markdown(f"""
    | | |
    |:---|---:|
    | Revenue protected | **${r['protected'] * acreage:,.0f}** |
    | Technology cost | ${r['cost_per_acre'] * acreage:,.0f} |
    | **Net benefit** | **${r['net_benefit'] * acreage:,.0f}** |
    """)


# ─── SOURCES TAB ─────────────────────────────────────────────────────

st.divider()

tab_sources, tab_assumptions = st.tabs(["Sources", "Assumptions & Limitations"])

with tab_sources:
    st.markdown("""
#### Primary Calibration Study

**Martinez-Luscher et al. (2020)** — "Mitigating Heat Wave and Exposure Damage to
'Cabernet Sauvignon' Wine Grape With Partial Shading Under Two Irrigation Amounts"
*Frontiers in Plant Science.* [PMC7683524](https://pmc.ncbi.nlm.nih.gov/articles/PMC7683524/)

> Cab Sauv, 4-day heatwave at ~105°F. Exposed: 24% cluster damage, 30-38% anthocyanin loss.
> Shaded (−7-11°F): 2% cluster damage, 20-23% anthocyanin loss.

#### Supporting Studies

| Study | Key Finding | Link |
|:------|:------------|:-----|
| Greer & Weedon (2013) | Semillon, 14-day heat: 30% berry damage, 55% ripening reduction | [PMC3848316](https://pmc.ncbi.nlm.nih.gov/articles/PMC3848316/) |
| Gambetta et al. (2021) | Sunburn review: 5-15% annual impact (AU), up to 30% must loss. Grade downgrade = ~50% value loss. Berry surface 12-15°C above air. | [PMC7819898](https://pmc.ncbi.nlm.nih.gov/articles/PMC7819898/) |
| Greer (2017) | 4 days at 40°C → 70% photosynthesis reduction, 12-day recovery | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0098847217300540) |
| Reshef et al. (2023) | LT50: 49.9°C at 30 min, 47.1°C at 90 min. Each +1 min = 3.34x damage probability | [PMC10083509](https://pmc.ncbi.nlm.nih.gov/articles/PMC10083509/) |
| Gonzalez Antivilo et al. (2022) | Pinot Noir: 13-16% anthocyanin reduction at just +1.5-2°C. Merlot: 0%. Pinot = "low plasticity" | [PMC9003205](https://pmc.ncbi.nlm.nih.gov/articles/PMC9003205/) |
| Lecourieux et al. (2017) | Malate at 30/25°C: 75% respired post-veraison vs 50% at 22/12°C | [PMC4955140](https://pmc.ncbi.nlm.nih.gov/articles/PMC4955140/) |
| Sweetman et al. (2014) | +3.4°C day heating over 11 days → 26% malate reduction | [PMC4203137](https://pmc.ncbi.nlm.nih.gov/articles/PMC4203137/) |
| Luo et al. (2011) | Repeated heat: 2nd exposure → sharper Rubisco decline, slower recovery | [PMC3162573](https://pmc.ncbi.nlm.nih.gov/articles/PMC3162573/) |

#### Economic Data

| Data Point | Value | Source |
|:-----------|:------|:-------|
| Sonoma Pinot Noir price/ton | $3,843 (2023 avg) | USDA NASS Grape Crush Report 2023, District 3 |
| Price range | \$500 - \$17,062/ton | Same |
| Yield assumption | 4.0 tons/acre | UC Davis Cost Study, Russian River Valley |
    """)

with tab_assumptions:
    st.markdown("""
#### Model Methodology

The model uses a **degree-hours framework** — cumulative hours × degrees above
physiological thresholds (95°F and 100°F) — to estimate crop damage. Each damage component
follows a **logistic saturation curve** calibrated to the Martinez-Luscher field study,
then adjusted for Pinot Noir sensitivity.

#### Assumption Confidence Ratings

| Parameter | Value | Confidence | How Derived |
|:----------|:------|:-----------|:------------|
| Sunburn at 24% / 4-day reference | 24% | **High** | Directly measured (PMC7683524) |
| Anthocyanin loss 30-38% reference | 34% | **High** | Directly measured (PMC7683524) |
| Berry surface +12-15°C above air | measured | **High** | Multiple studies |
| Pinot Noir 1.20x sensitivity | 1.20 | **Medium-High** | Cultivar comparison (PMC9003205) |
| Malic acid 22% reference | 22% | **Medium** | Multiple studies, interpolated |
| 10% daily compounding | 10% | **Medium** | Supported by Luo 2011 & Greer 2017; rate estimated |
| Berry shrivel 9% reference | 9% | **Medium** | Interpolated from 14-day Semillon study |
| Yield aggregation weights (0.35, 0.70) | — | **Medium** | Pattern in literature, not directly measured |
| Quality aggregation weights (0.45, 0.30, 0.08) | — | **Medium** | Contract structure + judgment |

#### What This Model Does NOT Account For

- **Irrigation effects** — extra irrigation can reduce berry temps and dehydration
- **Wind** — reduces sunburn significantly (not modeled; conservative for cooling benefit)
- **Light reduction** — our cooling also reduces light exposure, which provides additional sunburn protection not quantified in this model (conservative)
- **Timing within season** — heat at bloom vs veraison vs ripening has different effects
- **Vine age and health** — stressed or young vines may respond differently
- **Nighttime recovery** — Sonoma's large diurnal range aids recovery; not explicitly modeled
- **Market dynamics** — regional heat events can shift supply/demand pricing
- **Long-term vine damage** — repeated seasonal heatwaves could cause cumulative decline
    """)

