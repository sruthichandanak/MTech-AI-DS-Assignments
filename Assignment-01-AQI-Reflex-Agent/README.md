# AQI Reflex Agent 🌫️

A **simple reflex agent** that reads real-time pollutant data from nearby air-quality
sensors, calculates the **AQI using the India CPCB standard**, and classifies the air as
**low / moderate / high**.

> A *simple reflex agent* perceives the current environment and acts on
> **condition–action rules** — no memory, no learning.
>
> | Agent stage | Here |
> |-------------|------|
> | **Percept** | Pollutant concentrations from sensors near a location |
> | **Rules**   | CPCB sub-index formula → final AQI = max sub-index → band thresholds |
> | **Action**  | Output AQI value + classification (low / moderate / high) |

## How AQI is calculated (CPCB)

For each pollutant, a **sub-index** is computed by linear interpolation:

```
AQI_p = ((I_hi − I_lo) / (C_hi − C_lo)) × (C − C_lo) + I_lo
```

The **final AQI is the maximum** sub-index across all pollutants; that pollutant is the
"responsible/dominant" pollutant. Requires ≥3 pollutants including PM2.5 or PM10 (CPCB rule).

**Classification rules:**

| AQI      | Class    |
|----------|----------|
| 0–100    | low      |
| 101–200  | moderate |
| 201–500  | high     |

## Setup (one time)

```bash
# 1. install the dependency
pip install -r requirements.txt        # or: pip install requests

# 2. get a FREE OpenAQ API key -> https://explore.openaq.org (Account > API Keys)

# 3. create a file named  .env  in this folder with your key:
echo "OPENAQ_API_KEY=your_key_here" > .env
```
> `.env` is git-ignored, so your key stays private and is never pushed.

## Run — three easy ways

**A) Just run it — it asks you to type your coordinates:**
```bash
python3 aqi_agent.py
#   Latitude  : 19.9975
#   Longitude : 73.7898
```
Get the numbers from Google Maps: right-click your spot and copy them.

**B) By city name:**
```bash
python3 aqi_agent.py --city Delhi
python3 aqi_agent.py --city "Nashik"
```

**C) By exact coordinates on one line:**
```bash
python3 aqi_agent.py --lat 19.0760 --lon 72.8777      # Mumbai
```

Optional: pin a fixed location by setting `MY_LAT` / `MY_LON` at the top of
`aqi_agent.py` (then it won't ask). Testing without a key: `python3 aqi_agent.py --mock`

## Test
```bash
python3 tests/test_aqi.py
```

## Pollutants supported
PM2.5, PM10, NO₂, SO₂, O₃, CO, NH₃ — units µg/m³ (CO in mg/m³).

## Notes
- CPCB uses 24h averages (8h for CO/O₃); this reflex agent uses the latest instantaneous
  reading for simplicity.
- Data source: [OpenAQ](https://openaq.org). Swap `fetch_openaq()` for MQTT/serial to read
  from your own physical IoT sensors.
