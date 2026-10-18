"""Load raw API pulls into SQLite exactly as received (all text). No cleaning here."""
import json, csv, sqlite3, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
db = root / "data/processed/otr.db"
db.parent.mkdir(exist_ok=True)
if db.exists(): db.unlink()
con = sqlite3.connect(db)
con.execute("""CREATE TABLE raw_bts(indicator TEXT, measure1 TEXT, measure2 TEXT, units TEXT,
               date TEXT, value1 TEXT, note TEXT, source_file TEXT)""")
for f in ["bts_monthly_indicators.json", "bts_weekly_diesel_spot.json"]:
    for r in json.load(open(root / "data/raw" / f)):
        con.execute("INSERT INTO raw_bts VALUES (?,?,?,?,?,?,?,?)",
                    (r.get("indicator"), r.get("measure1"), r.get("measure2"), r.get("units"),
                     r.get("date"), r.get("value1"), r.get("note"), f))
con.execute("CREATE TABLE raw_eia(week_start TEXT, usd_per_gal TEXT)")
with open(root / "data/raw/eia_weekly_diesel.csv") as fh:
    for row in csv.DictReader(fh):
        con.execute("INSERT INTO raw_eia VALUES (?,?)", (row["week_start"], row["usd_per_gal"]))
con.commit()
print("raw_bts", con.execute("select count(*) from raw_bts").fetchone()[0],
      "raw_eia", con.execute("select count(*) from raw_eia").fetchone()[0])
