"""Re-download the raw files from the public APIs. NOT RUN in the original build environment
(outbound access to these hosts was blocked there); compare output with SOURCES.md before relying on it."""
import json, os, pathlib, urllib.parse, urllib.request, csv
raw = pathlib.Path(__file__).resolve().parents[1] / "data/raw"; raw.mkdir(parents=True, exist_ok=True)
BASE = "https://data.bts.gov/resource/y5ut-ibwt.json"
MONTHLY = ["Freight Transportation Services Index", "Producer Price Index for Trucking", "Producer Price Index: Diesel Fuel",
           "Number of Non-Farm Truck Transportation", "Number of Warehousing", "New Active Carriers Added",
           "Average Truck Speed in MPH at 10 Bottleneck", "Average Planning Time Index at 10 Bottleneck",
           "U.S. Goods Imports in Millions", "Personal Consumption Expenditures in Billions of $: Durable",
           "Total Business: Inventory to Sales", "Job Openings and Labor Turnover: Transportation", "Vehicle Miles Traveled"]
WEEKLY = ["U.S. Diesel Sales Prices", "Truck Spot Rates"]
def bts(prefixes, out):
    where = " OR ".join(f"indicator like '{p}%'" for p in prefixes)
    q = {"$select": "indicator,measure1,measure2,units,date,value1,note", "$where": where,
         "$order": "indicator,measure1,measure2,date", "$limit": "5000"}
    with urllib.request.urlopen(BASE + "?" + urllib.parse.urlencode(q)) as r: data = json.load(r)
    (raw / out).write_text(json.dumps(data)); print(out, len(data))
bts(MONTHLY, "bts_monthly_indicators.json"); bts(WEEKLY, "bts_weekly_diesel_spot.json")
key = os.environ["EIA_API_KEY"]
url = ("https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key=%s&frequency=weekly&data[0]=value"
       "&facets[series][]=EMD_EPD2D_PTE_NUS_DPG&start=2019-01-01&sort[0][column]=period&sort[0][direction]=asc&length=5000" % key)
with urllib.request.urlopen(url) as r: rows = json.load(r)["response"]["data"]
with open(raw / "eia_weekly_diesel.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["week_start", "usd_per_gal"]); [w.writerow([x["period"], x["value"]]) for x in rows]
print("eia_weekly_diesel.csv", len(rows))
