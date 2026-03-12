#!/usr/bin/env python3
"""
Crop Cooling Financial Model — Sonoma Pinot Noir
=================================================
Estimates yield and revenue protection from cooling technology
during extreme heat events (105°F, 5-day heatwave).

Uses a degree-hours framework calibrated against published viticulture
research. The key insight: cooling during the 4 hottest hours eliminates
~85% of degree-hours above the critical 100°F threshold (where berry
surface temperatures reach the 50°C necrosis zone), even though it
covers only 17% of the day.

Usage:
    python main.py
    Edit the Config section below to adjust assumptions.
"""

import math
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION — edit these to explore scenarios
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class GrapeConfig:
    """Grape economics. Defaults: Sonoma County Pinot Noir."""
    variety: str = "Pinot Noir"
    region: str = "Sonoma County"
    price_per_ton: float = 3_843.0        # 2023 USDA Crush Report, District 3
    yield_tons_per_acre: float = 4.0      # UC Davis Russian River Valley study
    heat_sensitivity: float = 1.20        # vs Cab Sauv (1.0); Pinot = thin skin,
                                          # cool-climate, low anthocyanin plasticity
                                          # (Gonzalez Antivilo et al. 2022)

    @property
    def revenue_per_acre(self) -> float:
        return self.price_per_ton * self.yield_tons_per_acre


@dataclass
class HeatConfig:
    """Heat wave parameters."""
    peak_temp_f: float = 105.0            # Daily peak air temperature (°F)
    overnight_low_f: float = 65.0         # Overnight minimum (°F)
    num_days: int = 5                     # Consecutive heat wave days


@dataclass
class CoolingConfig:
    """Technology deployment parameters."""
    cooling_delta_f: float = 4.5          # Temperature reduction (°F)
    cooling_hours: int = 4                # Hours of active cooling per day
    cost_labor: float = 200.0             # $/acre deployment
    cost_materials: float = 18.0          # $/acre materials

    @property
    def cost_per_acre(self) -> float:
        return self.cost_labor + self.cost_materials


# ═══════════════════════════════════════════════════════════════════════
# TEMPERATURE MODEL
# ═══════════════════════════════════════════════════════════════════════

def diurnal_temp(hour: float, peak: float, low: float) -> float:
    """
    Sinusoidal approximation of daily temperature.
    Peak at 3pm (hour 15), minimum at 3am (hour 3).
    """
    avg = (peak + low) / 2.0
    amp = (peak - low) / 2.0
    return avg + amp * math.sin(2.0 * math.pi * (hour - 9.0) / 24.0)


def hourly_temps(peak: float, low: float,
                 cooling_delta: float = 0.0,
                 cooling_hours: int = 0) -> list[tuple[int, float]]:
    """
    Generate 24 hourly temperatures for one day.
    If cooling is specified, it is applied during the N hottest hours.
    """
    raw = [(h, diurnal_temp(h, peak, low)) for h in range(24)]

    if cooling_hours > 0 and cooling_delta > 0:
        # Identify the hottest hours
        ranked = sorted(raw, key=lambda x: -x[1])
        cooled_set = {h for h, _ in ranked[:cooling_hours]}
        return [(h, t - cooling_delta if h in cooled_set else t)
                for h, t in raw]
    return raw


def degree_hours(temps: list[tuple[int, float]], threshold: float) -> float:
    """Cumulative degree-hours above a temperature threshold."""
    return sum(max(0.0, t - threshold) for _, t in temps)


# ═══════════════════════════════════════════════════════════════════════
# DAMAGE MODEL (research-calibrated)
# ═══════════════════════════════════════════════════════════════════════
#
# PRIMARY CALIBRATION — Martínez-Lüscher et al. (2020) PMC7683524
#   Cabernet Sauvignon, 4-day heatwave (~105°F peaks):
#   Exposed:  24% cluster damage, 30-38% anthocyanin loss, 17-27% flavonol loss
#   Shaded:   2% cluster damage,  20-23% anthocyanin loss, 0% flavonol loss
#
# SUPPORTING DATA:
#   Greer & Weedon (2013) PMC3848316
#     Semillon, 14-day heat: 30% berry damage, 55% ripening rate reduction
#   Gambetta et al. (2021) PMC7819898
#     Australia: 5-15% annual sunburn, up to 30% must yield loss
#     Grade downgrade (A→C/D): ~50% value loss
#     Berry surface temp: 12-15°C above air temp in direct sun
#   Greer (2017)
#     4 days at 40°C → 70% photosynthesis reduction, 12-day recovery
#   Reshef et al. (2023) PMC10083509
#     Each 1 min longer exposure → 3.34× higher damage probability
#     LT50 at 30 min = 49.9°C; at 90 min = 47.1°C
#   Gonzalez Antivilo et al. (2022) PMC9003205
#     Pinot Noir: 13-16% anthocyanin reduction at just +1.5-2°C
#     Merlot: 0% effect; Pinot classified as "low plasticity"
#   Lecourieux et al. (2017) PMC4955140
#     Malate at 30/25°C: 75% respired post-veraison vs 50% at 22/12°C
#   Sweetman et al. (2014) PMC4203137
#     +3.4°C day heating over 11 days → 26% malate reduction
#

@dataclass
class DamageEstimate:
    """Physiological damage from a heat event."""
    sunburn_pct: float           # Berry sunburn / necrosis
    shrivel_pct: float           # Berry dehydration / weight loss
    anthocyanin_loss_pct: float  # Color compound degradation
    acid_loss_pct: float         # Malic acid loss
    yield_loss_pct: float        # Net effective yield reduction
    quality_discount_pct: float  # Net price discount from quality loss


def _saturate(dh: float, ref_dh: float, ref_dmg: float,
              max_dmg: float, sensitivity: float = 1.0) -> float:
    """
    Logistic saturation model for crop damage.

    Damage approaches max_dmg asymptotically as degree-hours increase.
    Calibrated so that at dh=ref_dh (with sensitivity=1.0), damage=ref_dmg.
    Higher sensitivity (e.g. Pinot Noir=1.20) means damage accumulates faster.

    This avoids hard-cap artifacts where both cooled/uncooled hit the same
    ceiling and produce zero differentiation at extreme temperatures.
    """
    if dh <= 0:
        return 0.0
    if ref_dmg >= max_dmg:
        ref_dmg = max_dmg * 0.95
    k = -math.log(1.0 - ref_dmg / max_dmg) / ref_dh
    return max_dmg * (1.0 - math.exp(-k * sensitivity * dh))


def estimate_damage(heat: HeatConfig, grape: GrapeConfig,
                    cooling: CoolingConfig | None = None) -> DamageEstimate:
    """
    Estimate cumulative heat-wave damage using degree-hours framework.

    Maps cumulative degree-hours above physiological thresholds (95, 100, 105°F)
    to crop damage, calibrated against the Cab Sauv shading study.
    Uses logistic saturation curves so damage approaches a physical maximum
    asymptotically, always preserving differentiation between scenarios.
    """
    # --- Hourly temperatures (single day) ---
    if cooling:
        temps = hourly_temps(heat.peak_temp_f, heat.overnight_low_f,
                             cooling.cooling_delta_f, cooling.cooling_hours)
    else:
        temps = hourly_temps(heat.peak_temp_f, heat.overnight_low_f)

    dh95  = degree_hours(temps, 95.0)
    dh100 = degree_hours(temps, 100.0)

    # --- Multi-day compounding ---
    # Consecutive heat days compound damage: stressed vines can't recover
    # overnight (full recovery takes ~12 days; Greer 2017).
    # Each successive day, the vine is ~10% more vulnerable.
    compound_rate = 0.10
    day_multiplier = sum((1 + compound_rate) ** d
                         for d in range(heat.num_days))

    total_dh95  = dh95  * day_multiplier
    total_dh100 = dh100 * day_multiplier

    # --- Reference point (Cab Sauv 4-day study) ---
    # Uncooled single-day DH at 105°F peak / 65°F low:
    ref_temps = hourly_temps(105.0, 65.0)
    ref_dh100_day = degree_hours(ref_temps, 100.0)
    ref_dh95_day  = degree_hours(ref_temps, 95.0)

    ref_days = 4
    ref_mult = sum((1 + compound_rate) ** d for d in range(ref_days))

    ref_total_dh100 = ref_dh100_day * ref_mult   # ~85 DH
    ref_total_dh95  = ref_dh95_day  * ref_mult    # ~239 DH

    s = grape.heat_sensitivity    # Pinot Noir = 1.20

    # --- Component damage (logistic saturation) ---
    # Each component: _saturate(actual_DH, reference_DH, reference_damage,
    #                           physical_maximum, variety_sensitivity)

    # SUNBURN / NECROSIS: driven by DH above 100°F
    # At 100°F air, berry surface ≈ 50°C (necrosis threshold)
    # Ref: 24% at ~85 DH100 (Cab Sauv, 4-day); max ~50% (physical limit)
    sunburn = _saturate(total_dh100, ref_total_dh100, 0.24, 0.50, s)

    # BERRY SHRIVEL: cumulative dehydration from DH above 95°F
    # Ref: ~9% at ~239 DH95 (4-day); max ~20%
    shrivel = _saturate(total_dh95, ref_total_dh95, 0.09, 0.20, s)

    # ANTHOCYANIN LOSS: impaired above 95°F, accelerates above 100°F
    # Ref: 34% at ~239 DH95 (Cab Sauv, midpoint of 30-38%); max ~65%
    anthocyanin = _saturate(total_dh95, ref_total_dh95, 0.34, 0.65, s)

    # MALIC ACID LOSS: optimal 68-77°F, severely degraded above 95°F
    # Ref: ~22% at ~239 DH95 (4-day); max ~55%
    acid = _saturate(total_dh95, ref_total_dh95, 0.22, 0.55, s)

    # --- Aggregate into yield and quality impacts ---

    # Yield loss: sunburn destroys berries + shrivel reduces weight
    # Not all sunburned fruit is total loss (~35% translates to tonnage)
    yield_loss = min(0.50, sunburn * 0.35 + shrivel * 0.70)

    # Quality discount: color loss, acid loss, visible damage
    # For Pinot Noir: color = 45% of quality, acid = 30%, sunburn = 8%
    quality_discount = min(0.50,
                           anthocyanin * 0.45
                           + acid * 0.30
                           + sunburn * 0.08)

    return DamageEstimate(
        sunburn_pct=sunburn,
        shrivel_pct=shrivel,
        anthocyanin_loss_pct=anthocyanin,
        acid_loss_pct=acid,
        yield_loss_pct=yield_loss,
        quality_discount_pct=quality_discount,
    )


# ═══════════════════════════════════════════════════════════════════════
# FINANCIAL MODEL
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class FinancialResult:
    base_revenue: float
    uncooled_revenue: float
    cooled_revenue: float
    revenue_protected: float
    technology_cost: float
    net_benefit: float
    roi: float
    # Value decomposition
    yield_preservation_value: float
    quality_preservation_value: float
    # Damage details
    uncooled: DamageEstimate
    cooled: DamageEstimate


def run_model(heat: HeatConfig, grape: GrapeConfig,
              cooling: CoolingConfig) -> FinancialResult:
    """Run the full financial model and return results."""
    uncooled = estimate_damage(heat, grape, cooling=None)
    cooled   = estimate_damage(heat, grape, cooling=cooling)

    base = grape.revenue_per_acre

    uncooled_rev = base * (1 - uncooled.yield_loss_pct) \
                        * (1 - uncooled.quality_discount_pct)
    cooled_rev   = base * (1 - cooled.yield_loss_pct) \
                        * (1 - cooled.quality_discount_pct)

    protected = cooled_rev - uncooled_rev
    cost = cooling.cost_per_acre

    # Decompose revenue protection into yield vs quality components
    yl_u, yl_c = uncooled.yield_loss_pct, cooled.yield_loss_pct
    qd_u, qd_c = uncooled.quality_discount_pct, cooled.quality_discount_pct

    yield_value   = base * (yl_u - yl_c) * (1 - qd_u)
    quality_value = base * (1 - yl_c) * (qd_u - qd_c)

    return FinancialResult(
        base_revenue=base,
        uncooled_revenue=uncooled_rev,
        cooled_revenue=cooled_rev,
        revenue_protected=protected,
        technology_cost=cost,
        net_benefit=protected - cost,
        roi=protected / cost if cost > 0 else 0,
        yield_preservation_value=yield_value,
        quality_preservation_value=quality_value,
        uncooled=uncooled,
        cooled=cooled,
    )


# ═══════════════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════════════

W = 70  # output width


def fmt_pct(val: float) -> str:
    return f"{val:.1%}"


def print_header(heat: HeatConfig, grape: GrapeConfig, cooling: CoolingConfig):
    print()
    print("╔" + "═" * W + "╗")
    print("║" + " CROP COOLING FINANCIAL MODEL".center(W) + "║")
    print("║" + f" {grape.variety}, {grape.region}".center(W) + "║")
    print("╚" + "═" * W + "╝")
    print()
    print(f"  Scenario:  {heat.num_days}-day heatwave, {heat.peak_temp_f:.0f}°F "
          f"peak / {heat.overnight_low_f:.0f}°F overnight")
    print(f"  Grape:     {grape.variety} ({grape.region})")
    print(f"  Baseline:  ${grape.price_per_ton:,.0f}/ton  ×  "
          f"{grape.yield_tons_per_acre:.1f} tons/acre  =  "
          f"${grape.revenue_per_acre:,.0f}/acre")
    print(f"  Cooling:   −{cooling.cooling_delta_f:.1f}°F for "
          f"{cooling.cooling_hours} hrs/day (hottest hours)")
    print(f"  Cost:      ${cooling.cost_labor:.0f} labor + "
          f"${cooling.cost_materials:.0f} materials = "
          f"${cooling.cost_per_acre:.0f}/acre")


def print_degree_hours(heat: HeatConfig, cooling: CoolingConfig):
    """The core argument: 4 hours captures most of the damaging heat."""
    uncooled = hourly_temps(heat.peak_temp_f, heat.overnight_low_f)
    cooled   = hourly_temps(heat.peak_temp_f, heat.overnight_low_f,
                            cooling.cooling_delta_f, cooling.cooling_hours)

    print()
    print("─" * W)
    print("  DEGREE-HOURS ANALYSIS  (single day)")
    print("─" * W)
    print()

    print(f"  The {cooling.cooling_hours} hottest hours aren't 17% of the "
          "damage — they're where it concentrates:")
    print()

    for thresh in [95, 100, 105]:
        dh_u = degree_hours(uncooled, thresh)
        dh_c = degree_hours(cooled, thresh)
        red  = (1 - dh_c / dh_u) * 100 if dh_u > 0 else 0
        print(f"    Above {thresh}°F:  {dh_u:>5.1f} DH → {dh_c:>5.1f} DH    "
              f"({red:>4.0f}% reduction)")

    print()
    print("  Hourly temperatures (stress hours):")
    print(f"    {'Hour':>6}  {'Uncooled':>10}  {'Cooled':>10}  {'Δ':>8}")
    print(f"    {'─' * 6}  {'─' * 10}  {'─' * 10}  {'─' * 8}")

    for (h, tu), (_, tc) in zip(uncooled, cooled):
        if tu >= 90:
            d = tc - tu
            tag = "  ◄ cooled" if abs(d) > 0.1 else ""
            print(f"    {h:>4}:00  {tu:>8.1f}°F  {tc:>8.1f}°F  "
                  f"{d:>+6.1f}°F{tag}")


def print_damage(result: FinancialResult, heat: HeatConfig):
    uc, co = result.uncooled, result.cooled

    print()
    print("─" * W)
    print(f"  PHYSIOLOGICAL DAMAGE  ({heat.num_days}-day cumulative)")
    print("─" * W)
    print()

    rows = [
        ("Sunburn / necrosis",  uc.sunburn_pct,          co.sunburn_pct),
        ("Berry shrivel",       uc.shrivel_pct,          co.shrivel_pct),
        ("Anthocyanin loss",    uc.anthocyanin_loss_pct, co.anthocyanin_loss_pct),
        ("Malic acid loss",     uc.acid_loss_pct,        co.acid_loss_pct),
    ]

    print(f"    {'Category':<24} {'No cooling':>11} "
          f"{'With cooling':>13} {'Avoided':>9}")
    print(f"    {'─' * 24} {'─' * 11} {'─' * 13} {'─' * 9}")

    for name, u, c in rows:
        print(f"    {name:<24} {fmt_pct(u):>11} "
              f"{fmt_pct(c):>13} {fmt_pct(u - c):>9}")

    print()
    print(f"    {'─' * 60}")
    print(f"    {'=> Effective yield loss':<24} {fmt_pct(uc.yield_loss_pct):>11} "
          f"{fmt_pct(co.yield_loss_pct):>13} "
          f"{fmt_pct(uc.yield_loss_pct - co.yield_loss_pct):>9}")
    print(f"    {'=> Quality price disc.':<24} "
          f"{fmt_pct(uc.quality_discount_pct):>11} "
          f"{fmt_pct(co.quality_discount_pct):>13} "
          f"{fmt_pct(uc.quality_discount_pct - co.quality_discount_pct):>9}")


def print_financials(result: FinancialResult):
    base_loss   = result.base_revenue - result.uncooled_revenue
    cooled_loss = result.base_revenue - result.cooled_revenue

    print()
    print("─" * W)
    print("  FINANCIAL IMPACT  (per acre)")
    print("─" * W)
    print()
    print(f"    Baseline revenue (no heatwave):     ${result.base_revenue:>10,.0f}")
    print(f"    After heatwave, NO cooling:         "
          f"${result.uncooled_revenue:>10,.0f}   "
          f"(−${base_loss:,.0f})")
    print(f"    After heatwave, WITH cooling:       "
          f"${result.cooled_revenue:>10,.0f}   "
          f"(−${cooled_loss:,.0f})")
    print()
    print(f"    Revenue protected by cooling:       "
          f"${result.revenue_protected:>10,.0f}")
    print(f"      ├─ From yield preservation:       "
          f"${result.yield_preservation_value:>10,.0f}   "
          f"({result.yield_preservation_value / result.revenue_protected:.0%})")
    print(f"      └─ From quality preservation:     "
          f"${result.quality_preservation_value:>10,.0f}   "
          f"({result.quality_preservation_value / result.revenue_protected:.0%})")
    print()
    print(f"    Technology cost:                    "
          f"(${result.technology_cost:>10,.0f})")
    print(f"    ───────────────────────────────────────────")
    print(f"    NET BENEFIT:                        "
          f"${result.net_benefit:>10,.0f} /acre")
    print(f"    ROI:                                "
          f"{result.roi:>10.1f}x")


def print_scale(result: FinancialResult):
    print()
    print("─" * W)
    print("  SCALE ANALYSIS")
    print("─" * W)
    print()
    print(f"    {'Acres':>7}  {'Rev Protected':>14}  {'Cost':>10}  "
          f"{'Net Benefit':>12}  {'ROI':>6}")
    print(f"    {'─' * 7}  {'─' * 14}  {'─' * 10}  {'─' * 12}  {'─' * 6}")

    for acres in [10, 25, 50, 100, 250, 500]:
        rev  = result.revenue_protected * acres
        cost = result.technology_cost * acres
        net  = result.net_benefit * acres
        print(f"    {acres:>7,}  ${rev:>12,.0f}  ${cost:>8,.0f}  "
              f"${net:>10,.0f}  {result.roi:>5.1f}x")


def print_sensitivity(heat: HeatConfig, grape: GrapeConfig,
                      cooling: CoolingConfig):
    print()
    print("─" * W)
    print("  SENSITIVITY ANALYSIS")
    print("─" * W)

    # --- Peak temperature ---
    print(f"\n    {'Peak Temp':>14}  {'Net $/acre':>12}  {'ROI':>6}")
    print(f"    {'─' * 14}  {'─' * 12}  {'─' * 6}")
    for peak in [100, 102, 105, 108, 110, 115]:
        h = HeatConfig(peak_temp_f=float(peak),
                       overnight_low_f=heat.overnight_low_f,
                       num_days=heat.num_days)
        r = run_model(h, grape, cooling)
        tag = "  ◄" if peak == int(heat.peak_temp_f) else ""
        print(f"    {peak:>11}°F  ${r.net_benefit:>10,.0f}  "
              f"{r.roi:>5.1f}x{tag}")

    # --- Cooling delta ---
    print(f"\n    {'Cooling °F':>14}  {'Net $/acre':>12}  {'ROI':>6}")
    print(f"    {'─' * 14}  {'─' * 12}  {'─' * 6}")
    for delta in [3.0, 3.5, 4.0, 4.5, 5.0, 6.0]:
        c = CoolingConfig(cooling_delta_f=delta,
                          cooling_hours=cooling.cooling_hours,
                          cost_labor=cooling.cost_labor,
                          cost_materials=cooling.cost_materials)
        r = run_model(heat, grape, c)
        tag = "  ◄" if delta == cooling.cooling_delta_f else ""
        print(f"    {delta:>12.1f}°F  ${r.net_benefit:>10,.0f}  "
              f"{r.roi:>5.1f}x{tag}")

    # --- Grape price ---
    print(f"\n    {'Price $/ton':>14}  {'Net $/acre':>12}  {'ROI':>6}")
    print(f"    {'─' * 14}  {'─' * 12}  {'─' * 6}")
    prices = [
        (1_700, "Dist. avg"),
        (2_500, ""),
        (3_843, "Sonoma PN"),
        (5_000, ""),
        (8_000, "Premium"),
        (12_000, "Ultra-prem"),
    ]
    for price, label in prices:
        g = GrapeConfig(price_per_ton=float(price),
                        yield_tons_per_acre=grape.yield_tons_per_acre,
                        heat_sensitivity=grape.heat_sensitivity)
        r = run_model(heat, g, cooling)
        tag = f"  {label}" if label else ""
        print(f"    ${price:>11,}  ${r.net_benefit:>10,.0f}  "
              f"{r.roi:>5.1f}x{tag}")

    # --- Heatwave duration ---
    print(f"\n    {'Heat Days':>14}  {'Net $/acre':>12}  {'ROI':>6}")
    print(f"    {'─' * 14}  {'─' * 12}  {'─' * 6}")
    for days in [1, 2, 3, 5, 7, 10]:
        h = HeatConfig(peak_temp_f=heat.peak_temp_f,
                       overnight_low_f=heat.overnight_low_f,
                       num_days=days)
        r = run_model(h, grape, cooling)
        tag = "  ◄" if days == heat.num_days else ""
        print(f"    {days:>11} day{'s' if days != 1 else ' '}  "
              f"${r.net_benefit:>10,.0f}  {r.roi:>5.1f}x{tag}")

    # --- Cooling hours ---
    print(f"\n    {'Cool Hours':>14}  {'Net $/acre':>12}  {'ROI':>6}")
    print(f"    {'─' * 14}  {'─' * 12}  {'─' * 6}")
    for hrs in [2, 3, 4, 5, 6, 8]:
        c = CoolingConfig(cooling_delta_f=cooling.cooling_delta_f,
                          cooling_hours=hrs,
                          cost_labor=cooling.cost_labor,
                          cost_materials=cooling.cost_materials)
        r = run_model(heat, grape, c)
        tag = "  ◄" if hrs == cooling.cooling_hours else ""
        print(f"    {hrs:>11} hrs  ${r.net_benefit:>10,.0f}  "
              f"{r.roi:>5.1f}x{tag}")


def print_sources():
    print()
    print("─" * W)
    print("  DATA SOURCES")
    print("─" * W)
    print("""
    PRICING
      USDA NASS California Grape Crush Report 2023, District 3
      Sonoma Pinot Noir weighted average: $3,843/ton
      Range: $500 - $17,062/ton (quality-dependent)

    YIELD
      UC Davis Cost & Return Study, Russian River Valley
      Pinot Noir: 4.0 tons/acre assumed average

    DAMAGE MODEL CALIBRATION
      Primary: Martínez-Lüscher et al. (2020) PMC7683524
        Cab Sauv, 4-day heatwave at 105°F:
        Exposed:  24% cluster damage, 30-38% anthocyanin loss
        Shaded:   2% cluster damage,  20-23% anthocyanin loss

      Greer & Weedon (2013) PMC3848316
        Semillon, 14-day heat: 30% berry damage, 55% ripening reduction

      Gambetta et al. (2021) PMC7819898
        5-15% annual sunburn (AU); up to 30% must yield loss
        Grade downgrade (A→C/D) = ~50% value loss
        Berry surface: 12-15°C above air temp in sun

      Greer (2017): 4 days at 40°C → 70% photosynthesis reduction,
        12-day recovery (basis for compounding model)

      Reshef et al. (2023) PMC10083509
        LT50: 49.9°C at 30 min, 47.1°C at 90 min
        Each +1 min exposure = 3.34× damage probability

    METHODOLOGY
      Degree-hours above 95/100°F thresholds
      Logistic saturation damage curves (asymptotic, no hard caps)
      Sinusoidal diurnal temperature model (peak 3pm, min 3am)
      10% daily compounding for multi-day events
      1.20× Pinot Noir sensitivity factor vs Cab Sauv baseline
        (Gonzalez Antivilo et al. 2022, PMC9003205)
    """)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    heat    = HeatConfig()
    grape   = GrapeConfig()
    cooling = CoolingConfig()

    result = run_model(heat, grape, cooling)

    print_header(heat, grape, cooling)
    print_degree_hours(heat, cooling)
    print_damage(result, heat)
    print_financials(result)
    print_scale(result)
    print_sensitivity(heat, grape, cooling)
    print_sources()
    print()


if __name__ == "__main__":
    main()
