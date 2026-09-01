"""
Simple Reflex Agent for Air Quality Index (AQI)
================================================
Standard : India CPCB (National Air Quality Index)
Data      : Public API (OpenAQ) with a mock fallback for offline testing.

A simple reflex agent = perceive -> apply condition-action rules -> act.
    percept  : raw pollutant concentrations from sensors near a location
    reasoning: CPCB sub-index formula, final AQI = max sub-index
    action   : classify as low / moderate / high and output the value

Run:
    python aqi_agent.py                 # mock data (no key needed)
    python aqi_agent.py --lat 18.52 --lon 73.85          # real, needs key
    export OPENAQ_API_KEY=xxxx          # free key from https://openaq.org
"""

from __future__ import annotations
import argparse
import os
import sys

# ==========================================================================
#  OPTIONAL: pin a fixed location here.
#  If you fill in both numbers, running `python3 aqi_agent.py` will use this
#  spot without asking. Leave them as None to be PROMPTED to type the
#  latitude/longitude in the terminal each time.
#  Tip: get coordinates from Google Maps (right-click a spot -> copy numbers).
# ==========================================================================
MY_LAT = None      # e.g. 19.9975   (None = ask me in the terminal)
MY_LON = None      # e.g. 73.7898   (None = ask me in the terminal)

# --------------------------------------------------------------------------
# 1. CPCB BREAKPOINT TABLES
# --------------------------------------------------------------------------
# Each row: (C_low, C_high, I_low, I_high)
# Concentration units: ug/m3, except CO which is mg/m3.
# Averaging period per CPCB: 24h for PM2.5/PM10/SO2/NO2/NH3, 8h for CO/O3.
# A true reflex agent uses instantaneous readings (see caveat in README notes).

BREAKPOINTS = {
    "pm25": [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200),
             (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)],
    "pm10": [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200),
             (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)],
    "no2":  [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200),
             (180, 280, 201, 300), (280, 400, 301, 400), (400, 1000, 401, 500)],
    "so2":  [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200),
             (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2000, 401, 500)],
    "o3":   [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200),
             (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)],
    "co":   [(0, 1.0, 0, 50), (1.0, 2.0, 51, 100), (2.0, 10, 101, 200),
             (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)],
    "nh3":  [(0, 200, 0, 50), (200, 400, 51, 100), (400, 800, 101, 200),
             (800, 1200, 201, 300), (1200, 1800, 301, 400), (1800, 3000, 401, 500)],
}

# CPCB 6-band labels for reporting the responsible pollutant's band.
CPCB_BANDS = [(0, 50, "Good"), (51, 100, "Satisfactory"), (101, 200, "Moderate"),
              (201, 300, "Poor"), (301, 400, "Very Poor"), (401, 500, "Severe")]


# --------------------------------------------------------------------------
# 2. AQI CALCULATION (the agent's reasoning)
# --------------------------------------------------------------------------
def sub_index(pollutant: str, conc: float) -> float | None:
    """CPCB linear-interpolation sub-index for one pollutant reading."""
    if pollutant not in BREAKPOINTS or conc is None or conc < 0:
        return None
    for c_lo, c_hi, i_lo, i_hi in BREAKPOINTS[pollutant]:
        if c_lo <= conc <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (conc - c_lo) + i_lo)
    return 500  # above the highest breakpoint -> capped at Severe


def calculate_aqi(readings: dict[str, float]) -> dict:
    """
    Final AQI = MAX of all valid sub-indices (CPCB method).
    CPCB validity rule: need >= 3 pollutants AND at least one of PM2.5/PM10.
    """
    sub = {p: sub_index(p, c) for p, c in readings.items()}
    sub = {p: v for p, v in sub.items() if v is not None}

    has_pm = any(p in sub for p in ("pm25", "pm10"))
    if len(sub) < 3 or not has_pm:
        return {"valid": False, "reason": "Need >=3 pollutants incl. PM2.5 or PM10",
                "sub_indices": sub}

    dominant = max(sub, key=sub.get)
    aqi = sub[dominant]
    band = next(name for lo, hi, name in CPCB_BANDS if lo <= aqi <= hi)
    return {"valid": True, "aqi": aqi, "dominant_pollutant": dominant,
            "cpcb_band": band, "sub_indices": sub}


# --------------------------------------------------------------------------
# 3. CLASSIFICATION (the condition-action rules)
# --------------------------------------------------------------------------
def classify(aqi: int) -> str:
    """Simple reflex rules -> low / moderate / high."""
    if aqi <= 100:
        return "low"
    elif aqi <= 200:
        return "moderate"
    return "high"


# --------------------------------------------------------------------------
# 4. SENSOR INPUT (the percept) -- Public API + mock fallback
# --------------------------------------------------------------------------
def fetch_mock(lat: float, lon: float) -> dict[str, float]:
    """Deterministic sample readings so the agent runs with no network/key."""
    return {"pm25": 85, "pm10": 140, "no2": 55, "so2": 20, "co": 1.4, "o3": 60}


POLLUTANTS = {"pm25", "pm10", "no2", "so2", "o3", "co", "nh3"}
def _is_mass_unit(units: str) -> bool:
    """True for ug/m3 or mg/m3, whatever mu/superscript variant the API sends."""
    u = (units or "").replace("µ", "u").replace("μ", "u").replace("³", "3").lower()
    return u in ("ug/m3", "mg/m3")


def geocode_city(name: str) -> tuple[float, float, str]:
    """Turn a city name into (lat, lon, label) using Open-Meteo's free
    geocoding API (no API key required)."""
    import requests
    r = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                     params={"name": name, "count": 1, "language": "en"},
                     timeout=15).json()
    hits = r.get("results")
    if not hits:
        raise ValueError(f"Could not find a place called '{name}'.")
    h = hits[0]
    label = ", ".join(x for x in (h.get("name"), h.get("admin1"),
                                  h.get("country")) if x)
    return h["latitude"], h["longitude"], label


def prompt_lat_lon() -> tuple[float, float, str]:
    """Ask the user to type their latitude and longitude in the terminal.
    (Tip: in Google Maps, right-click your spot and copy the two numbers.)"""
    print("\nEnter your location coordinates "
          "(Google Maps: right-click a spot -> copy the numbers):")
    while True:
        try:
            lat = float(input("  Latitude  : ").strip())
            lon = float(input("  Longitude : ").strip())
            return lat, lon, "entered coordinates"
        except ValueError:
            print("  ! Please enter numbers only, e.g. 19.9975 (no comma, no text).")
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            sys.exit(1)

def _get_json(url: str, headers: dict, params: dict | None = None) -> dict:
    """GET + surface API errors instead of silently returning no results."""
    import requests
    r = requests.get(url, headers=headers, params=params, timeout=20)
    if r.status_code in (401, 403):
        raise RuntimeError(
            f"OpenAQ rejected the API key (HTTP {r.status_code}: {r.text[:120]}).\n"
            "  * Check .env has no quotes or spaces around the key\n"
            "  * A brand-new key can take a few minutes to activate\n"
            "  * Confirm it at https://explore.openaq.org > Account > API Keys"
        )
    if r.status_code == 429:
        raise RuntimeError("OpenAQ rate limit hit (HTTP 429). Wait a minute and retry.")
    r.raise_for_status()
    return r.json()

def fetch_openaq(lat: float, lon: float, radius_m: int = 25000) -> dict[str, float]:
    """
    Pull latest concentrations from the nearest OpenAQ station.

    OpenAQ v3 keeps readings per *sensor id*, so for each station we first map
    sensor id -> (pollutant, units), then read /latest and translate. We scan the
    nearest stations and pick the one with the FRESHEST (newest) valid data, so
    you get live readings rather than whichever station happened to be closest.

    Unit handling (important for a correct CPCB AQI):
      * CPCB breakpoints use ug/m3 for all pollutants EXCEPT CO, which is mg/m3.
      * OpenAQ reports CO in ug/m3, so we divide CO by 1000 -> mg/m3.
      * Stations often expose the same gas twice (ug/m3 AND ppb). We only accept
        mass-concentration units (ug/m3 / mg/m3) and skip ppb/ppm sensors.
    Returns {pollutant: value, _station, _time}  (ug/m3, CO in mg/m3).
    """
    import requests  # imported lazily so mock mode has zero deps

    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAQ_API_KEY (free from https://explore.openaq.org).")

    headers = {"X-API-Key": key}
    locs = _get_json(
        "https://api.openaq.org/v3/locations", headers,
        params={"coordinates": f"{lat},{lon}", "radius": radius_m, "limit": 50},
    ).get("results", [])

    best: dict[str, float] = {}
    candidates: list[dict] = []
    for loc in locs[:8]:  # scan up to 8 nearest, then choose the freshest
        sid_info = {s["id"]: ((s.get("parameter") or {}).get("name"),
                              (s.get("parameter") or {}).get("units"))
                    for s in loc.get("sensors", [])}
        latest = _get_json(
            f"https://api.openaq.org/v3/locations/{loc['id']}/latest", headers,
        ).get("results", [])

        readings: dict[str, float] = {}
        newest = ""
        for row in latest:
            param, units = sid_info.get(row.get("sensorsId"), (None, None))
            val = row.get("value")
            if param not in POLLUTANTS or val is None or param in readings:
                continue
            if not _is_mass_unit(units):         # skip ppb/ppm duplicates
                continue
            val = float(val)
            if param == "co" and not (units or "").lower().startswith("mg"):
                val /= 1000.0                     # ug/m3 -> mg/m3 for CPCB
            readings[param] = val
            ts = (row.get("datetime") or {}).get("utc") or ""
            newest = max(newest, ts)              # ISO strings sort chronologically

        has_pm = any(p in readings for p in ("pm25", "pm10"))
        if len(readings) >= 3 and has_pm:
            readings["_station"] = loc.get("name", str(loc.get("id")))
            readings["_time"] = newest
            candidates.append(readings)
        elif len(readings) > len(best):
            best = readings

    if candidates:  # prefer the station whose newest reading is most recent
        return max(candidates, key=lambda r: r.get("_time", ""))
    return best


# --------------------------------------------------------------------------
# 5. THE AGENT LOOP
# --------------------------------------------------------------------------
def run_agent(lat: float, lon: float, use_mock: bool) -> dict:
    # -- perceive --
    try:
        readings = fetch_mock(lat, lon) if use_mock else fetch_openaq(lat, lon)
    except RuntimeError as e:
        return {"error": str(e)}
    if not readings:
        return {"error": "No sensor data found near this location."}
    station = readings.pop("_station", "mock" if use_mock else "unknown")
    reading_time = readings.pop("_time", "")

    # -- reason --
    result = calculate_aqi(readings)
    if not result["valid"]:
        return {"error": result["reason"], "sensor_readings": readings,
                "station": station}

    # -- act --
    result["classification"] = classify(result["aqi"])
    result["sensor_readings"] = readings
    result["location"] = {"lat": lat, "lon": lon}
    result["station"] = station
    result["reading_time"] = reading_time
    return result


def freshness(iso_utc: str) -> tuple[str, bool]:
    """Return a human 'age' string and whether the data is stale (>3h old)."""
    from datetime import datetime, timezone
    if not iso_utc:
        return "unknown", True
    try:
        t = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        secs = (datetime.now(timezone.utc) - t).total_seconds()
    except ValueError:
        return iso_utc, True
    stale = secs > 3 * 3600
    if secs < 3600:
        return f"{int(secs // 60)} min ago", stale
    if secs < 86400:
        return f"{secs / 3600:.1f} hours ago", stale
    return f"{secs / 86400:.1f} days ago", stale


def load_env() -> None:
    """Read a local .env file (KEY=value lines) into the environment.
    Tolerates a UTF-8 BOM (Windows PowerShell/Notepad), wrapping quotes and an
    `export ` prefix, and warns about common misnamed files."""
    folder = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(folder, ".env")
    if not os.path.exists(env_path):
        for wrong in (".env.txt", "env", "env.txt", ".env.example"):
            if os.path.exists(os.path.join(folder, wrong)):
                print(f"Note: found '{wrong}' — the file must be named exactly '.env'")
        return
    with open(env_path, encoding="utf-8-sig") as fh:   # utf-8-sig strips the BOM
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")        # drop wrapping quotes
            os.environ.setdefault(k.strip(), v)


def resolve_location(args) -> tuple[float, float, str]:
    """Decide which coordinates to use, in priority order:
       1. explicit --lat/--lon   2. --city <name>
       3. saved MY_LAT/MY_LON    4. ask the user to type them in."""
    if args.lat is not None and args.lon is not None:
        return args.lat, args.lon, "given coordinates"
    if args.city:
        lat, lon, label = geocode_city(args.city)
        print(f"Resolved '{args.city}' -> {label} ({lat}, {lon})")
        return lat, lon, label
    if MY_LAT is not None and MY_LON is not None:  # location set in the file
        print(f"Using your saved location -> ({MY_LAT}, {MY_LON})")
        return MY_LAT, MY_LON, "saved location"
    return prompt_lat_lon()  # no input given -> ask in the terminal


def main() -> None:
    load_env()  # pick up OPENAQ_API_KEY from .env automatically
    p = argparse.ArgumentParser(description="Simple reflex AQI agent (CPCB, live data).")
    p.add_argument("--city", type=str, help="City/area name, e.g. --city Delhi")
    p.add_argument("--lat", type=float, help="Latitude (use with --lon)")
    p.add_argument("--lon", type=float, help="Longitude (use with --lat)")
    p.add_argument("--mock", action="store_true",
                   help="Use sample data instead of live sensors (for testing only).")
    args = p.parse_args()

    if not args.mock and not os.environ.get("OPENAQ_API_KEY"):
        print("\nNo OpenAQ API key found.\n"
              "  1. Get a FREE key at https://explore.openaq.org (Account -> API Keys)\n"
              "  2. Create a file named .env next to this script containing:\n"
              "         OPENAQ_API_KEY=your_key_here\n"
              "  Then run again. (Or run with --mock to try sample data.)")
        sys.exit(1)

    if args.mock:
        lat, lon = 19.9975, 73.7898
    else:
        try:
            lat, lon, _ = resolve_location(args)
        except Exception as e:
            print(f"\nCould not determine location: {e}")
            sys.exit(1)

    out = run_agent(lat, lon, use_mock=args.mock)

    print("\n=== Simple Reflex AQI Agent (India CPCB) ===")
    if "error" in out:
        print("Error:", out["error"])
        if "sensor_readings" in out:
            print("Readings:", out["sensor_readings"])
        sys.exit(1)

    age, stale = freshness(out.get("reading_time", ""))
    print(f"Location          : {out['location']['lat']}, {out['location']['lon']}")
    print(f"Station           : {out['station']}")
    print(f"Reading time (UTC): {out.get('reading_time') or 'unknown'}   ({age})")
    print(f"Sensor readings   : {out['sensor_readings']}")
    print(f"Sub-indices       : {out['sub_indices']}")
    print(f"Dominant pollutant: {out['dominant_pollutant']}")
    print(f"AQI VALUE         : {out['aqi']}  (CPCB: {out['cpcb_band']})")
    print(f"CLASSIFICATION    : {out['classification'].upper()}")
    if stale:
        print("\n⚠  WARNING: this reading is NOT live — the sensor last reported "
              f"{age}.\n   Government sensors often lag. Try --city <other city> "
              "for a station\n   that is reporting more recently.")


if __name__ == "__main__":
    main()
