# Crop Cooling Financial Model: Sources & Assumptions

**Model purpose:** Estimate yield and revenue protection for Sonoma County Pinot Noir
wine grapes from cooling technology deployed during extreme heat events (105°F, 5-day heatwave).

**Important:** This model is built on published viticulture research, but applies that
research to a specific scenario through calibrated extrapolation. Where direct data exists,
we cite it. Where we interpolate or make judgment calls, we flag it explicitly.

---

## 1. Grape Economics

### Price per ton: $3,843

- **Source:** USDA NASS California Grape Crush Report 2023, District 3 (Sonoma & Marin Counties), Pinot Noir weighted average.
- **Link:** https://www.nass.usda.gov/Statistics_by_State/California/Publications/Specialty_and_Other_Releases/Grapes/Crush/Reports/index.php
- **Supporting:** Vintroux analysis of 2023-2024 crush data (https://vineyardandwinerysales.com/blog/napa-valley-and-sonoma-county-wine-grape-prices-2024/)
- **Range in data:** $250 - $60,000/ton in 2023 (quality-dependent). Premium Russian River Valley fruit commands 10-30%+ above county average.
- **Confidence:** HIGH. This is official USDA data.

### Yield: 4.0 tons/acre

- **Source:** UC Davis Cost & Return Study, Russian River Valley Pinot Noir (2017).
- **Link:** https://coststudyfiles.ucdavis.edu/uploads/cs_public/c6/28/c6287d1a-64b9-4ba6-b8ff-d83d6c0d0a64/amendedwinegrapessonomafinaldraft91817.pdf
- **Note:** This is the assumed average yield over the vineyard's productive life. Actual yields vary by year, block, and management (3-6 tons/acre is typical for premium Sonoma Pinot).
- **Confidence:** HIGH. Standard industry figure from UC Davis.

### Technology cost: $380/acre ($200 labor + $180 materials)

- **Source:** Provided by the company.
- **Confidence:** HIGH (internal data).

---

## 2. Temperature Model

### Sinusoidal diurnal curve (peak 3pm, min 3am)

- **Method:** T(hour) = avg + amplitude * sin(2pi(hour - 9)/24), where avg = (peak + low)/2 and amplitude = (peak - low)/2.
- **Basis:** Standard approximation in agroclimate modeling. Real diurnal curves can be asymmetric (faster morning rise, slower evening decline), but sinusoidal is widely used and close enough for degree-hour calculations.
- **Assumption:** Peak at 3pm, minimum at 3am. In Sonoma, summer peaks typically occur between 2-5pm. The specific hour shifts the cooling window but doesn't materially change degree-hour totals.
- **Confidence:** HIGH for the methodology. The exact curve shape matters less than the total degree-hours, which are robust to minor shape variations.

### Degree-hours above thresholds (95, 100°F)

- **Method:** For each hour, sum max(0, temp - threshold). This captures both intensity and duration of heat exposure.
- **Basis:** Degree-day and degree-hour accumulation models are standard in plant physiology and have been used in viticulture for decades (e.g., Winkler Index for growing degree-days).
- **Key finding:** On a 105°F peak day, cooling the 4 hottest hours by 4.5°F reduces degree-hours above 100°F by 85% and above 95°F by 35%.
- **Confidence:** HIGH. This is physics/math, not an assumption.

---

## 3. Damage Model

The model estimates four types of physiological damage, each driven by degree-hours above
a relevant temperature threshold. All damage curves use logistic saturation (damage approaches
a physical maximum asymptotically), calibrated against a primary reference study.

### Primary calibration study

**Martinez-Luscher et al. (2020)**
"Mitigating Heat Wave and Exposure Damage to 'Cabernet Sauvignon' Wine Grape With
Partial Shading Under Two Irrigation Amounts"
- **Journal:** Frontiers in Plant Science
- **PMC:** PMC7683524
- **Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7683524/
- **Design:** Field study on Cabernet Sauvignon during a 4-day heatwave (~103-106°F peaks). Compared exposed vines vs. vines under 40% shade nets.
- **Key results used:**
  - Exposed: 24% cluster damage, 30-38% anthocyanin degradation, 17-27% flavonol loss
  - Shaded: 2% cluster damage, 20-23% anthocyanin degradation, 0% flavonol loss
  - Shading reduced cluster temperatures by 3.9-6°C (7-11°F)
  - TSS: 27.2 Brix (exposed) vs 24.7 Brix (shaded)
- **How we use it:** This is the anchor point for all damage curves. We compute degree-hours for the study's conditions (4 days at ~105°F peak) and fit each damage curve to pass through the measured data point.
- **Limitation:** Study was on Cabernet Sauvignon, not Pinot Noir. We apply a sensitivity multiplier (see below) to adjust.
- **Confidence:** HIGH for the data. The study is peer-reviewed, field-based, and directly relevant.

### 3a. Sunburn / Necrosis

- **What it measures:** Percentage of berries with visible sunburn damage (browning, necrosis, tissue death).
- **Threshold:** Driven by degree-hours above 100°F. At 100°F air temperature, sun-exposed berry surfaces reach ~50°C, which is the necrosis threshold.
- **Reference data point:** 24% cluster damage at ~85 cumulative DH above 100°F (4-day, Cab Sauv).
- **Physical maximum:** 50%. Not every berry faces the sun; interior and shaded berries are protected.
- **Supporting evidence for the 100°F/50°C berry surface link:**
  - Gambetta et al. (2021), PMC7819898: Berry surface temps run 12-15°C above air temperature in direct sun (citing Smart & Sinclair, 1976).
  - Muller et al. (2023), PMC10083509: LT50 (temperature killing 50% of berries at 30 min exposure) = 49.9°C. At 90 min = 47.1°C. Each additional minute of exposure increases damage probability 3.34x.
- **Confidence:** HIGH. Direct field measurement, strong mechanistic basis.

### 3b. Berry Shrivel (Dehydration)

- **What it measures:** Berry weight loss from heat-driven dehydration.
- **Threshold:** Driven by degree-hours above 95°F (cumulative stress, not just peak damage).
- **Reference data point:** ~9% weight loss at ~239 cumulative DH above 95°F (4-day equivalent).
- **Physical maximum:** 20%.
- **How the reference was derived:** The Semillon 14-day study (Greer & Weedon 2013, PMC3848316) found 30% berry damage over 14 days, but this included sunburn. Separating shrivel from sunburn, and scaling to 4 days, gives roughly 9%. This is an interpolation.
- **Supporting evidence:**
  - Greer & Weedon (2013), PMC3848316: 30% total berry damage, 55% ripening rate reduction over 14 days at 40°C. Yield itself was not significantly affected (berries shriveled but stayed on vine).
  - IVES Technical Reviews: Berry shrivel can reduce yields by 25%+ in bad years.
  - Martinez-Luscher et al. (2020): Shaded berries at 80% irrigation had "meaningfully higher berry mass" vs exposed.
- **Limitation:** The 9% figure is interpolated, not directly measured for a 4-day event. Could plausibly be 5-15%.
- **Confidence:** MEDIUM. Directionally correct, magnitude is estimated.

### 3c. Anthocyanin Loss (Color Degradation)

- **What it measures:** Reduction in anthocyanin concentration (the pigments that give red wine its color).
- **Threshold:** Driven by degree-hours above 95°F.
- **Reference data point:** 34% loss at ~239 DH above 95°F (4-day, Cab Sauv; midpoint of 30-38% range).
- **Physical maximum:** 65%.
- **Supporting evidence:**
  - Martinez-Luscher et al. (2020), PMC7683524: 30-38% anthocyanin degradation in exposed Cab Sauv vs 20-23% in shaded.
  - de Rosas et al. (2022), PMC9003205: Pinot Noir showed 13.3-16.4% anthocyanin reduction with just +1.5-2°C warming. Merlot showed 0%.
  - Progressive Crop Consultant (2025): Anthocyanin synthesis impaired above 95°F, degradation increases.
- **Why it matters for Pinot Noir:** Anthocyanin/color IS the varietal identity. Pinot has lower total anthocyanin than Cab Sauv, and "color where grapes are sunburned is not extractable" (Good Fruit Grower). Any color loss hits Pinot disproportionately.
- **Confidence:** HIGH for the reference data. The 34% Cab Sauv figure is directly measured; the extrapolation to other conditions via the saturation curve adds moderate uncertainty.

### 3d. Malic Acid Loss

- **What it measures:** Reduction in malic acid, the primary organic acid that gives wine its crisp acidity.
- **Threshold:** Driven by degree-hours above 95°F.
- **Reference data point:** ~22% loss at ~239 DH above 95°F (4-day equivalent).
- **Physical maximum:** 55%.
- **How the reference was derived:** This is a composite estimate from multiple studies:
  - Rienth et al. (2016), PMC4955140: In controlled environment, malate at hot conditions (30/25°C day/night) was 85 uEq vs 230 uEq at cool conditions (22/12°C) at ripening — 63% less. But this compares hot vs. cool over the full ripening period, not a 4-day event vs. baseline.
  - Sweetman et al. (2014), PMC4203137: Day heating (+4-6°C above control) over 11 days produced ~25% malate reduction (85.8 to 63.3 umol/berry). Scaling to 4 days at more extreme heating gives ~20-25%.
  - Frontiers in Plant Physiology (2025): Pinot Noir bunch heating study confirmed "hastened reduction in malic acid concentration" with +10°C heating for 7 days.
  - Progressive Crop Consultant (2025): "Malate accumulation is optimal between 68 to 77°F and significantly degraded above 105°F."
- **Limitation:** No single study measures exactly "22% malate loss in 4 days at 105°F." The figure is inferred from multiple data points at different conditions.
- **Confidence:** MEDIUM. Well-supported directionally. The 22% figure is consistent with the range implied by the literature, but involves interpolation.

---

## 4. Pinot Noir Sensitivity Multiplier: 1.20x

This multiplier adjusts all damage curves to account for Pinot Noir's greater heat
vulnerability compared to Cabernet Sauvignon (the variety in our primary calibration study).

### Evidence

**de Rosas et al. (2022), PMC9003205:**
"High Temperature Alters Anthocyanin Concentration and Composition in Grape Berries of
Malbec, Merlot, and Pinot Noir in a Cultivar-Dependent Manner"
- Field study comparing three varieties under identical +1.5-2°C heating.
- Results:
  - Pinot Noir: 13.3% (2017) and 16.4% (2018) anthocyanin reduction at harvest (p < 0.01 both years)
  - Merlot: 0% reduction (unaffected)
  - Pinot Noir classified as having "low plasticity" — it cannot shift its anthocyanin profile to compensate
  - Pinot Noir does not produce acylated anthocyanins, which other varieties use as a protective mechanism
  - Pinot Noir was THE ONLY cultivar with statistically significant harvest-time anthocyanin reduction

**Additional qualitative support:**
- Pinot Noir has thinner skin than Cabernet Sauvignon (widely documented in viticulture textbooks and industry sources)
- Pinot Noir is classified as a cool-climate variety that "struggles to retain acidity in the heat" (Press Democrat, Sonoma County)
- Wine Enthusiast: "incredibly sensitive to shifts in heat, humidity, and sunlight"

### How 1.20x was chosen

- The Gonzalez Antivilo study shows Pinot Noir is clearly more sensitive than Merlot (which showed 0% effect) and responds differently than Malbec (which showed larger effects but at veraison, not harvest).
- For anthocyanin sensitivity specifically, a higher multiplier (1.25-1.30x) might be justified.
- For sunburn/necrosis, the multiplier is based on thinner skin (qualitative; not precisely quantified in literature).
- 1.20x is a blended estimate across all damage types — conservative for quality, moderate for yield.
- **This is a judgment call.** A defensible range would be 1.10-1.30x.

### Confidence: MEDIUM-HIGH

Directionally well-supported by peer-reviewed cultivar comparison. The specific magnitude (1.20x vs 1.15x or 1.25x) is judgment, but the model's sensitivity analysis shows results are not dramatically sensitive to this parameter.

---

## 5. Multi-Day Compounding: 10% per day

### What it models

On day 1 of a heatwave, the vine is at baseline. On day 2, it hasn't fully recovered
from day 1's stress, so the same degree-hours cause more damage. We model this as a
10% increase in effective vulnerability per consecutive day.

Over 5 days, the cumulative multiplier is:
1.0 + 1.1 + 1.21 + 1.331 + 1.464 = 6.105 (vs 5.0 with no compounding).

### Evidence

**Greer (2017):**
- 4 days at 40°C caused 70% photosynthesis reduction.
- Full recovery took 12 days.
- This means vines cannot recover between consecutive heatwave days.

**Luo et al. (2011), PMC3162573:**
"Photosynthetic Responses to Heat Treatments at Different Temperatures and following
Recovery in Grapevine Leaves"
- After 2nd exposure at 45°C, Rubisco activation state declined MORE than after 1st stress.
- Recovery after 2nd stress was SLOWER than after 1st stress.
- At 40°C, recovery from 2nd stress took until Day 6, vs faster recovery after 1st.

**Soil water availability study (2024), Springer:**
- Well-watered vines could recover after a 6-day heatwave (Tmax 40°C).
- Drought-stressed vines could NOT resume PSII performance after even 1 day of recovery.

### How 10% was chosen

- The literature clearly shows compounding exists and is meaningful.
- No study directly quantifies a "per-day compounding rate."
- 10% produces a 5-day multiplier of 6.1x (22% more total damage than simple 5x), which is moderate.
- The Greer 2017 result (70% photosynthesis loss over 4 days) suggests substantial compounding but doesn't translate directly to a daily rate.
- A defensible range would be 5-15%.

### Confidence: MEDIUM

The phenomenon is well-documented. The specific rate is estimated.

---

## 6. Yield Aggregation Weights

### Formula

```
yield_loss = sunburn × 0.35 + shrivel × 0.70
```

### Interpretation

- **Sunburn × 0.35:** Not all sunburned clusters are total yield losses. The Martinez-Luscher study noted ~1/3 of damaged clusters were "severe." The 0.35 factor means about 35% of sunburn translates to actual tonnage reduction; the rest manifests as quality degradation (counted separately).
- **Shrivel × 0.70:** Berry weight loss more directly reduces tonnage, but some shriveled berries still get harvested (at higher Brix). The Semillon study found yield "was not affected" despite 30% berry damage, because shriveled berries stayed on the vine. The 0.70 factor accounts for this partial offset.

### Supporting evidence

- Martinez-Luscher et al. (2020): 24% cluster damage, of which "more than one-third was categorized as severe."
- Greer & Weedon (2013): "Yield was not affected" despite 30% berry damage (Semillon).
- Gambetta et al. (2021): Grade downgrade from A to C/D = ~50% value loss.

### Confidence: MEDIUM

The structure (sunburn + shrivel = yield loss, with partial conversion factors) is sound. The specific weights (0.35, 0.70) are judgment estimates based on the pattern in the literature. No single study provides these exact coefficients.

---

## 7. Quality Discount Aggregation Weights

### Formula

```
quality_discount = anthocyanin × 0.45 + acid × 0.30 + sunburn × 0.08
```

### Interpretation

This maps physiological damage to a price-per-ton reduction. The weights reflect how
wineries assess grape quality when making purchasing decisions.

- **Anthocyanin × 0.45:** Color is the dominant quality factor for Pinot Noir. Wineries pay premiums for deep, well-developed color. "Color where grapes are sunburned is not extractable" (Good Fruit Grower). For Pinot specifically, which already has lower anthocyanin than Cab Sauv, any color loss disproportionately impacts value.
- **Acid × 0.30:** Acidity (driven by malic acid) provides structure and freshness. Heat-stressed Pinot loses its signature crisp acidity, producing "flabby" wines that can't command premium prices.
- **Sunburn × 0.08:** Visible berry damage (brown spots, necrosis) directly affects winery acceptance. This is a smaller weight because most of sunburn's economic impact is captured through yield loss and anthocyanin degradation.

### Supporting evidence for quality-based pricing

- **Grape purchase contracts** (Extension.org): Include bonuses for narrow Brix/pH ranges and penalties for substandard fruit. Wineries can reject or renegotiate price for defects including raisining and visual damage.
- **Michael David Winery example:** $25/ton bonus per 0.5 Brix increment; 15% premium for quality growers.
- **Sonoma County pricing range:** $250 - $60,000/ton (2023) for the same variety in the same county, demonstrating massive quality-based pricing spread.
- **Australian grading (Gambetta et al. 2021):** Grade downgrade from A to C/D = ~50% value loss. This provides a ceiling reference.
- **Model output check:** The model produces ~31% quality discount for uncooled 5-day heat-stressed Pinot Noir. This means grapes that would normally sell at $3,843/ton sell at ~$2,650/ton. This sits between "lose your premium" (10-30% above average) and "total downgrade" (50% loss) — consistent with severe but not catastrophic heat damage.

### Confidence: MEDIUM

The structure is well-supported (wineries do price on color, acid, and visual quality). The specific weights are judgment. No published study directly maps "X% anthocyanin loss = Y% price reduction."

---

## 8. Logistic Saturation Curve

### Formula

```
damage = max_damage × (1 - e^(-k × sensitivity × degree_hours))
```

Where k is calibrated so that at the reference degree-hours (with sensitivity = 1.0),
the damage equals the reference measurement.

### Why this shape

- **Linear models** would predict unlimited damage at extreme conditions (e.g., 200% berry loss), which is physically impossible.
- **Hard caps** create artifacts where both cooled and uncooled scenarios hit the same ceiling, showing zero benefit from cooling at extreme temperatures.
- **Logistic saturation** naturally approaches a maximum while always preserving differentiation between scenarios. This matches biological reality: damage increases rapidly at first, then slows as the most vulnerable tissue is already affected.

### Confidence: HIGH for the methodology

This is a standard approach in biological dose-response modeling. The specific maximum values for each component (50% sunburn, 20% shrivel, 65% anthocyanin, 55% acid) are judgment estimates of physical limits.

---

## 9. What This Model Does NOT Account For

Transparency requires noting what's excluded:

- **Irrigation effects:** The Martinez-Luscher study showed irrigation level (40% vs 80% ET) had "mild effects" on berry temperature and dehydration. Our model doesn't vary irrigation.
- **Vine age and health:** Older or stressed vines may be more vulnerable. The calibration study used established, commercially managed vines.
- **Timing within season:** Heat stress at bloom vs veraison vs ripening has very different effects. We model a generic "during growing season" event.
- **Wind:** Muller et al. (2023) found wind significantly reduces sunburn. Our model assumes calm conditions (conservative for the cooling benefit).
- **Light reduction:** Shade nets in the calibration study reduced both temperature AND light (60% PAR reduction). Our cooling technology reduces temperature only, not light. This means our sunburn estimates may be slightly conservative (light also drives sunburn independently of temperature).
- **Nighttime temperatures:** The model uses overnight lows but doesn't explicitly model night recovery. Sonoma's diurnal range (often 30-40°F) provides better overnight recovery than inland regions.
- **Long-term vine damage:** Repeated heatwaves across seasons could cause cumulative vine decline. This model is single-event only.
- **Market dynamics:** Price per ton varies with supply/demand, not just fruit quality. A heat wave affecting the entire region could shift pricing in complex ways.

---

## 10. Full Reference List

1. **Martinez-Luscher J, et al. (2020).** "Mitigating Heat Wave and Exposure Damage to 'Cabernet Sauvignon' Wine Grape With Partial Shading Under Two Irrigation Amounts." *Frontiers in Plant Science.* PMC7683524. https://pmc.ncbi.nlm.nih.gov/articles/PMC7683524/

2. **Greer DH, Weedon MM (2013).** "The impact of high temperatures on Vitis vinifera cv. Semillon grapevine performance and berry ripening." *Frontiers in Plant Science.* PMC3848316. https://pmc.ncbi.nlm.nih.gov/articles/PMC3848316/

3. **Gambetta JM, et al. (2021).** "Sunburn in Grapes: A Review." *Frontiers in Plant Science.* PMC7819898. https://pmc.ncbi.nlm.nih.gov/articles/PMC7819898/

4. **Greer DH (2017).** "Responses of biomass accumulation, photosynthesis and the net carbon budget to high canopy temperatures of Vitis vinifera L. cv. Semillon vines grown in field conditions." *Environmental and Experimental Botany.* https://www.sciencedirect.com/science/article/abs/pii/S0098847217300540

5. **Muller K, Keller M, Stoll M, Friedel M (2023).** "Wind speed, sun exposure and water status alter sunburn susceptibility of grape berries." *Frontiers in Plant Science.* PMC10083509. https://pmc.ncbi.nlm.nih.gov/articles/PMC10083509/

6. **de Rosas I, Deis L, Baldo Y, Cavagnaro JB, Cavagnaro PF (2022).** "High Temperature Alters Anthocyanin Concentration and Composition in Grape Berries of Malbec, Merlot, and Pinot Noir in a Cultivar-Dependent Manner." *Plants.* PMC9003205. https://pmc.ncbi.nlm.nih.gov/articles/PMC9003205/

7. **Rienth M, Torregrosa L, Sarah G, Ardisson M, Brillouet JM, Romieu C (2016).** "Temperature desynchronizes sugar and organic acid metabolism in ripening grapevine fruits and remodels their transcriptome." *BMC Plant Biology.* PMC4955140. https://pmc.ncbi.nlm.nih.gov/articles/PMC4955140/

8. **Sweetman C, et al. (2014).** "Metabolic effects of elevated temperature on organic acid degradation in ripening Vitis vinifera fruit." *Journal of Experimental Botany.* PMC4203137. https://pmc.ncbi.nlm.nih.gov/articles/PMC4203137/

9. **Luo HB, et al. (2011).** "Photosynthetic Responses to Heat Treatments at Different Temperatures and following Recovery in Grapevine (Vitis amurensis L.) Leaves." *PLOS ONE.* PMC3162573. https://pmc.ncbi.nlm.nih.gov/articles/PMC3162573/

10. **USDA NASS (2024).** California Grape Crush Report 2023, Final. District 3 (Sonoma/Marin). https://www.nass.usda.gov/Statistics_by_State/California/Publications/Specialty_and_Other_Releases/Grapes/Crush/Reports/index.php

12. **UC Davis (2017).** Cost and Return Study: Wine Grapes, Sonoma County, Russian River Valley. https://coststudyfiles.ucdavis.edu/

13. **Progressive Crop Consultant (2025).** "Effect of Heat on Grapevine Production and Fruit Quality." https://progressivecrop.com/2025/03/18/effect-of-heat-on-grapevine-production-and-fruit-quality/

---

## 11. Assumption Confidence Summary

| Parameter | Value | Confidence | Basis |
|-----------|-------|------------|-------|
| Grape price ($/ton) | $3,843 | HIGH | USDA Crush Report 2023 |
| Yield (tons/acre) | 4.0 | HIGH | UC Davis cost study |
| Technology cost | $380/acre | HIGH | Company data |
| Degree-hours calculation | computed | HIGH | Physics / math |
| Sunburn at 24%/4-day reference | 24% | HIGH | Field study (PMC7683524) |
| Anthocyanin loss 30-38% reference | 34% | HIGH | Same study |
| Berry surface +12-15°C above air | measured | HIGH | Multiple studies |
| Pinot Noir 1.20x sensitivity | 1.20 | MEDIUM-HIGH | Cultivar comparison (PMC9003205) |
| Malic acid 22% reference | 22% | MEDIUM | Multiple studies, interpolated |
| 10% daily compounding | 10% | MEDIUM | Supported by Luo 2011, Greer 2017; rate estimated |
| Berry shrivel 9% reference | 9% | MEDIUM | Interpolated from 14-day study |
| Yield aggregation weights | 0.35, 0.70 | MEDIUM | Pattern in literature, not directly measured |
| Quality aggregation weights | 0.45, 0.30, 0.08 | MEDIUM | Contract structure + judgment |
| Saturation curve maximums | varies | MEDIUM | Physical limit estimates |
