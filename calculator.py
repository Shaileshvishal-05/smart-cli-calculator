import csv
import json
import re
import urllib.request
from datetime import datetime

history = []
LIVE_RATES = {}

# Physical measurements mapped to base units (length: meters, time: seconds)
UNIT_TABLES = {
    # Length
    "m": ("length", 1.0),
    "km": ("length", 1000.0),
    "cm": ("length", 0.01),
    "mm": ("length", 0.001),
    "mi": ("length", 1609.34),
    "ft": ("length", 0.3048),
    "inch": ("length", 0.0254),
    "in": ("length", 0.0254),
    # Time
    "s": ("time", 1.0),
    "sec": ("time", 1.0),
    "min": ("time", 60.0),
    "minute": ("time", 60.0),
    "minutes": ("time", 60.0),
    "h": ("time", 3600.0),
    "hr": ("time", 3600.0),
    "hour": ("time", 3600.0),
    "hours": ("time", 3600.0),
    "day": ("time", 86400.0),
    "days": ("time", 86400.0),
    # Offline Currency Fallback (Base: 1 USD)
    "usd": ("currency", 1.0),
    "eur": ("currency", 0.92),
    "inr": ("currency", 83.5),
    "gbp": ("currency", 0.79),
    "jpy": ("currency", 155.0),
    "cad": ("currency", 1.36),
    "aud": ("currency", 1.52),
    "aed": ("currency", 3.67),
    "sar": ("currency", 3.75),
    "sgd": ("currency", 1.35),
    "chf": ("currency", 0.90),
    "cny": ("currency", 7.23),
    "rub": ("currency", 92.0),
    "brl": ("currency", 5.15),
    "krw": ("currency", 1370.0),
    "mxn": ("currency", 16.8),
}

# Aliases for colloquial names and words
CURRENCY_ALIASES = {
    "dollar": "usd",
    "dollars": "usd",
    "buck": "usd",
    "bucks": "usd",
    "rupee": "inr",
    "rupees": "inr",
    "rs": "inr",
    "pound": "gbp",
    "pounds": "gbp",
    "yen": "jpy",
    "euro": "eur",
    "euros": "eur",
    "dirham": "aed",
    "dirhams": "aed",
    "riyal": "sar",
    "riyals": "sar",
    "dinar": "kwd",
    "dinars": "kwd",
    "yuan": "cny",
    "won": "krw",
    "rand": "zar",
    "ruble": "rub",
    "rubles": "rub",
    "baht": "thb",
    "peso": "mxn",
    "pesos": "mxn",
}


def fetch_live_rates():
    """Fetches real-time exchange rates for 160+ currencies relative to USD."""
    global LIVE_RATES
    url = "https://open.er-api.com/v6/latest/USD"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("result") == "success":
                LIVE_RATES = {k.lower(): v for k, v in data["rates"].items()}
                print("✓ Live currency rates updated (160+ currencies loaded)!")
    except Exception as e:
        print(f"⚠ Warning: Could not fetch live rates ({e}). Using offline units.")


def convert_units(amount: float, from_unit: str, to_unit: str):
    u1, u2 = from_unit.lower(), to_unit.lower()

    # Map colloquial names/words (e.g. 'dirhams' -> 'aed')
    u1 = CURRENCY_ALIASES.get(u1, u1)
    u2 = CURRENCY_ALIASES.get(u2, u2)

    # 1. Live Currency Rates (Supports 160+ ISO currency codes)
    if u1 in LIVE_RATES and u2 in LIVE_RATES:
        usd_val = amount / LIVE_RATES[u1]
        final_val = usd_val * LIVE_RATES[u2]
        return round(final_val, 4)

    # 2. Offline Fallback Currencies & Physical Units (length, time)
    if u1 not in UNIT_TABLES or u2 not in UNIT_TABLES:
        return "Unknown unit or currency code!"

    cat1, factor1 = UNIT_TABLES[u1]
    cat2, factor2 = UNIT_TABLES[u2]

    if cat1 != cat2:
        return f"Cannot convert {cat1} into {cat2}!"

    val_in_base = amount * factor1
    final_val = val_in_base / factor2
    return round(final_val, 4)


def save_to_csv():
    with open("calc_history.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(history)
    print("History saved to calc_history.csv!")


# Fetch live rates once at startup
fetch_live_rates()

print("--- Unit & Currency Calculator ---")
print("Math: '10 + 5' | Convert: '100 km to mi' or '250 aed to inr'")

while True:
    val = input("\nEnter query (or 'h' for history, 'q' to quit): ").strip()

    if not val:
        continue

    cmd = val.lower()
    if cmd == "q":
        if history:
            save_to_csv()
        break

    if cmd == "h":
        if not history:
            print("History is empty.")
        else:
            for row in history:
                print(f"{row[0]} | {row[1]} = {row[2]}")
        continue

    # 1. Unit & Currency Conversion
    convert_match = re.match(
        r"^([0-9.]+)\s*([a-zA-Z]+)\s+(?:to|in)\s+([a-zA-Z]+)$", val, re.IGNORECASE
    )

    if convert_match:
        amount, from_unit, to_unit = convert_match.groups()
        result = convert_units(float(amount), from_unit, to_unit)

        print(f"Result: {result} {to_unit.upper()}")
        if not str(result).startswith("Cannot") and not str(result).startswith("Unknown"):
            history.append(
                [
                    datetime.now().strftime("%H:%M:%S"),
                    f"{amount} {from_unit} -> {to_unit}",
                    f"{result} {to_unit.upper()}",
                ]
            )
        continue

    # 2. Standard Arithmetic
    try:
        parts = val.split()
        if len(parts) != 3:
            raise ValueError

        num1, op, num2 = float(parts[0]), parts[1], float(parts[2])

        ops = {
            "+": num1 + num2,
            "-": num1 - num2,
            "*": num1 * num2,
            "/": num1 / num2 if num2 != 0 else "Error: Division by Zero",
        }

        result = ops.get(op, "Invalid Operator")
        print(f"Result: {result}")

        if not str(result).startswith("Error") and result != "Invalid Operator":
            history.append(
                [
                    datetime.now().strftime("%H:%M:%S"),
                    f"{num1} {op} {num2}",
                    result,
                ]
            )

    except ValueError:
        print("Format error! Examples:")
        print("  Math:     12 * 8")
        print("  Currency: 250 aed to inr  (or usd, eur, gbp, jpy, etc.)")
        print("  Units:    5 km to m")