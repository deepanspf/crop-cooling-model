# Crop Cooling Financial Model: How It Works

## The Science: What Heat Does to Wine Grapes

### Sunburn / Necrosis

This is literal tissue death. When berry surface temperature exceeds ~50C (122F) — which happens when air temp hits ~100F because sun-exposed berries run 12-15C hotter than air — the skin cells die. You see brown patches, cracking, and dried-out spots. It's the same mechanism as a sunburn on human skin: thermal damage to living cells, compounded by UV radiation.

Severe sunburn = the berry is physically destroyed. Moderate sunburn = the berry survives but with damaged skin that can't function properly (which cascades into the other problems below).

**Timing:** Happens within hours of exposure. Research shows 10% damage probability after just 15 minutes at 50C berry surface, 50% after 30 minutes, 90% after 90 minutes.

### Berry Shrivel (Dehydration)

This is water loss. Under heat stress, the berry loses water through transpiration faster than the vine can resupply it through the xylem and phloem. The berry literally shrinks — like a grape turning into a raisin, but while still on the vine.

This is different from sunburn: a shriveled berry may have no visible burn damage, but it weighs less. Since grapes are sold by the ton, lighter berries = less revenue. Shriveled berries also have concentrated sugars (higher Brix) which sounds good but actually causes problems — the sugar/acid balance gets thrown off, leading to wines that are high in alcohol but lack freshness.

**Timing:** Gradual over days. Cumulative — gets worse with each consecutive hot day.

### Anthocyanin Loss (Color Degradation)

Anthocyanins are the pigments in grape skin that make red wine red. They're synthesized by the vine during ripening, but heat disrupts this process in two ways:

1. **Synthesis slows down** — the enzymes that build anthocyanins work poorly above 95F
2. **Degradation speeds up** — existing anthocyanins break down faster at high temperatures

The net result: the grapes lose color. For Pinot Noir specifically, this is devastating because Pinot already has less anthocyanin than thicker-skinned varieties like Cab Sauv or Syrah. There's less buffer. The Gonzalez Antivilo study showed Pinot Noir loses 13-16% of its anthocyanin with just a 1.5-2C temperature increase, while Merlot lost 0%.

Crucially, Pinot Noir was classified as having "low plasticity" — it can't compensate by shifting to different types of anthocyanins the way Malbec can. What it loses, it loses permanently.

**Why it matters financially:** Winemakers assess grape color at delivery. Pale, washed-out Pinot Noir signals heat damage and commands a lower price. And as one source noted: "color where grapes are sunburned is not extractable" — you can't even get the remaining pigment out during winemaking.

**Timing:** Takes 2+ days to manifest in measurable composition changes, but the enzymatic disruption starts within hours.

### Malic Acid Loss (Acidity Degradation)

Grapes contain two main acids: tartaric acid (stable, doesn't change much with heat) and malic acid (the same acid in green apples — very temperature-sensitive). Malic acid is what gives wine its crisp, fresh character.

The vine uses malic acid as fuel through respiration, and respiration rate roughly doubles for every 18F temperature increase. So at 105F, the vine is burning through its malic acid reserves far faster than normal. The controlled environment studies showed: at 30/25C, berries lost 75% of their malate post-veraison vs only 50% at 22/12C.

The result is wine that tastes "flabby" or "flat" — lacking the acidity that provides structure, freshness, and aging potential. For Pinot Noir, which is prized for its bright acidity and elegance, this is a major quality hit.

**Timing:** Continuous process that accelerates with temperature. The acid is being consumed every hour the vine is hot, not just during peak temps.

### How They Interact

These aren't independent — they compound:

- **Sunburn damages skin** -> damaged skin can't synthesize anthocyanins -> color loss accelerates
- **Dehydration concentrates sugars** -> sugar/acid ratio gets worse -> vine respires more malic acid trying to manage the imbalance
- **Photosynthesis shuts down above 105F** -> vine can't produce energy from sunlight -> relies even more on burning malic acid reserves for energy
- **Multi-day compounding** -> the vine can't recover overnight (takes ~12 days), so day 2 starts from a worse baseline than day 1

This is why a 5-day heatwave is so much worse than 5 separate hot days: the vine enters a downward spiral where each day's damage makes the next day's damage worse.

### Why Our Cooling Targets the Right Things

The model shows cooling is most effective at preventing sunburn (85% of degree-hours above 100F eliminated) and moderately effective at reducing quality degradation (35% of degree-hours above 95F eliminated). This maps to the physics:

- **Sunburn is threshold-driven** (100F air -> 50C berry surface) — cooling below the threshold prevents it almost entirely
- **Anthocyanin and acid loss are cumulative** (every hour above 95F contributes) — cooling helps but doesn't eliminate the uncooled morning/evening hours that are still above 95F

---

## The Model: Step by Step

### Step 1: Temperature Curve

For each of the 5 days, the model generates 24 hourly temperatures using a sine wave:

```
T(hour) = average + amplitude x sin(phase)
```

With a 105F peak / 65F low, the average is 85F and amplitude is 20F. The curve peaks at 3pm and bottoms at 3am. This gives temperatures like:

```
6am: 71F -> 10am: 90F -> 1pm: 102F -> 3pm: 105F -> 6pm: 99F -> 10pm: 80F
```

Since each day's peak is set independently (e.g. 101, 103, 107, 105, 100), each day gets its own curve.

### Step 2: Apply Cooling

The model finds the N hottest hours in each day (default 4) and subtracts the cooling effect (default 4.5F) from those hours only. The rest of the day is untouched.

This produces two temperature profiles per day — uncooled and cooled.

### Step 3: Degree-Hours

For each day, at each threshold (95F and 100F), the model sums up "how many degrees above the threshold, for how many hours":

```
DH = sum of max(0, temp - threshold) for each hour
```

Example for a 105F day, above 100F:
- 1pm is 102.3F -> contributes 2.3
- 2pm is 104.3F -> contributes 4.3
- 3pm is 105F -> contributes 5.0
- ... total = 18.3 DH uncooled, 2.8 DH cooled

This is where the core argument lives: **cooling 4 hours eliminates 85% of DH above 100F**.

### Step 4: Multi-Day Compounding

Each successive day's degree-hours are multiplied by a compounding factor (10% per day), because stressed vines can't recover overnight:

- Day 1: x 1.00
- Day 2: x 1.10
- Day 3: x 1.21
- Day 4: x 1.33
- Day 5: x 1.46

The compounded DH from all 5 days are summed into total_dh95 and total_dh100 — one set for uncooled, one for cooled.

### Step 5: Damage Estimation (4 Components)

Each damage type is a logistic saturation curve — it rises quickly at low degree-hours, then flattens as it approaches a physical maximum:

```
damage = max_damage x (1 - e^(-k x sensitivity x degree_hours))
```

The k constant is calibrated so the curve passes through a known research data point. All four curves use the same structure:

| Component | Driven by | Reference data point | Physical max |
|-----------|-----------|---------------------|-------------|
| **Sunburn** | DH above 100F | 24% at ~85 DH (Cab Sauv, 4 days) | 50% |
| **Berry shrivel** | DH above 95F | 9% at ~239 DH (4 days) | 20% |
| **Anthocyanin loss** | DH above 95F | 34% at ~239 DH (Cab Sauv, 4 days) | 65% |
| **Acid loss** | DH above 95F | 22% at ~239 DH (4 days) | 55% |

The sensitivity parameter (1.20 for Pinot Noir) makes damage accumulate 20% faster than the Cab Sauv baseline.

This step runs twice — once with uncooled DH, once with cooled DH — producing two damage profiles.

### Step 6: Aggregate into Yield Loss and Quality Discount

The four components feed into two financial outputs:

**Yield loss** (tons you lose):
```
yield_loss = sunburn x 0.35 + shrivel x 0.70
```
Sunburn's weight is lower (0.35) because not all sunburned clusters are total losses — about 1/3 is severe. Shrivel directly reduces berry weight so it has a higher conversion (0.70).

**Quality discount** (price reduction per ton):
```
quality_discount = anthocyanin x 0.45 + acid x 0.30 + sunburn x 0.08
```
Color (anthocyanin) is weighted highest because for Pinot Noir, color IS the varietal identity. Acid affects wine balance. Sunburn's small weight here avoids double-counting with yield.

### Step 7: Revenue Calculation

```
revenue = (price per ton) x (yield per acre) x (1 - yield_loss) x (1 - quality_discount)
```

This runs for both scenarios:
- **Uncooled**: higher yield loss + higher quality discount = lower revenue
- **Cooled**: lower yield loss + lower quality discount = higher revenue

**Revenue protected** = cooled revenue - uncooled revenue

**Net benefit** = revenue protected - technology cost ($380/acre)

**ROI** = revenue protected / technology cost

### Step 8: Value Decomposition

The revenue protected is split into two sources:
- **Yield preservation value** = extra tons saved x price at uncooled quality
- **Quality preservation value** = better price per ton x cooled tonnage

This shows where the money comes from — roughly 47% yield, 53% quality for the default scenario.

---

**The whole chain**: per-day temperatures -> hourly curves -> cooling applied -> degree-hours above thresholds -> compounding across days -> logistic damage curves (x4) -> yield loss + quality discount -> revenue comparison -> net benefit and ROI.
