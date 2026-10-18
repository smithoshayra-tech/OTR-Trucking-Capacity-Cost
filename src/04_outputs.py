"""Charts (PNG) and Tableau-ready CSV extracts. Reads results.json and the SQLite tables only."""
import sqlite3, json, pathlib
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
root = pathlib.Path(__file__).resolve().parents[1]
con = sqlite3.connect(root / "data/processed/otr.db")
R = json.load(open(root / "data/processed/results.json"))
df = pd.read_csv(root / "data/processed/features_with_changes.csv", parse_dates=["month"]).set_index("month")
out = root / "outputs"; out.mkdir(exist_ok=True)
NAVY, ORANGE, GREY, TEAL = "#1F3864", "#C55A11", "#7F7F7F", "#2E8B8B"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold"})

# 1. Diesel vs trucking prices (2019-01 = 100)
fig, ax = plt.subplots(figsize=(9, 4.2))
base = df[["ppi_trucking_gf", "diesel_usd_gal"]].dropna()
ax.plot(base.index, 100 * base.ppi_trucking_gf / base.ppi_trucking_gf.iloc[0], color=NAVY, lw=2, label="Trucking price index (PPI, general freight)")
ax.plot(base.index, 100 * base.diesel_usd_gal / base.diesel_usd_gal.iloc[0], color=ORANGE, lw=2, label="Diesel price per gallon")
for t in ["2022-03", "2026-03"]: ax.axvline(pd.Timestamp(t + "-01"), color=GREY, ls=":", lw=1)
ax.text(pd.Timestamp("2022-03-01"), 84, " Mar 2022 shock", fontsize=8, color=GREY, va="bottom")
ax.text(pd.Timestamp("2026-03-01"), 84, "Mar 2026 shock ", fontsize=8, color=GREY, va="bottom", ha="right")
ax.set_ylabel("Index (Jan 2019 = 100)"); ax.set_title("Diesel moves fast; trucking prices follow, but by much less"); ax.legend(frameon=False, fontsize=9)
fig.text(0.01, 0.01, "Sources: BTS Supply Chain & Freight Indicators; EIA. Monthly, Jan 2019 to Aug 2026.", fontsize=7, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out / "01_diesel_vs_trucking_prices.png", dpi=160); plt.close(fig)

# 2. Pass-through scatter on month-over-month changes
d = df[["ppi_mom", "diesel_mom"]].dropna()
x = d.diesel_mom.rolling(1).sum()
fig, ax = plt.subplots(figsize=(6.4, 4.6))
ax.scatter(d.diesel_mom, d.ppi_mom, s=22, color=NAVY, alpha=.65)
for t, lab in [("2022-03-01", "Mar 2022"), ("2026-03-01", "Mar 2026"), ("2026-04-01", "Apr 2026")]:
    ax.annotate(lab, (d.loc[t, "diesel_mom"], d.loc[t, "ppi_mom"]), textcoords="offset points", xytext=(6, -10), fontsize=8, color=ORANGE)
b = np.polyfit(d.diesel_mom, d.ppi_mom, 1); xs = np.linspace(d.diesel_mom.min(), d.diesel_mom.max(), 50)
ax.plot(xs, b[0] * xs + b[1], color=ORANGE, lw=1.6)
ax.set_xlabel("Diesel price change, month over month (%)"); ax.set_ylabel("Trucking price change, month over month (%)")
ax.set_title("A 10% diesel jump moves trucking prices about 1.3%\nin the same month (about 2.2% within three)", fontsize=10.5)
fig.tight_layout(); fig.savefig(out / "02_passthrough_scatter.png", dpi=160); plt.close(fig)

# 3. Out-of-time test
rows = []
for h, lab in [("h0", "Same month\n(nowcast)"), ("h1", "1 month ahead"), ("h3", "3 months ahead")]:
    for k, kl in [("naive", "Average only"), ("fuel", "Fuel-based"), ("fuel_capacity", "Fuel + capacity")]:
        rows.append({"horizon": lab, "model": kl, "rmse": R["oos_expanding_window"][h][k]["rmse"], "mae": R["oos_expanding_window"][h][k]["mae"]})
t = pd.DataFrame(rows)
fig, ax = plt.subplots(figsize=(8, 4.2)); w = .26
for i, (k, c) in enumerate(zip(["Average only", "Fuel-based", "Fuel + capacity"], [GREY, NAVY, TEAL])):
    s = t[t.model == k]; ax.bar(np.arange(3) + (i - 1) * w, s.rmse, w, color=c, label=k)
    for xx, v in zip(np.arange(3) + (i - 1) * w, s.rmse): ax.text(xx, v + .03, f"{v:.2f}", ha="center", fontsize=8)
ax.set_xticks(range(3)); ax.set_xticklabels(t.horizon.unique()); ax.set_ylabel("Forecast error (RMSE, % points)")
ax.set_ylim(0, 3.3); ax.set_title("Out-of-time test (Jan 2024 to Aug 2026): fuel helps in the current month; the edge fades after that"); ax.title.set_fontsize(10); ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper center")
fig.tight_layout(); fig.savefig(out / "03_out_of_time_test.png", dpi=160); plt.close(fig)

# 4. Capacity context
c = df[["truck_emp_k", "new_carriers_total"]].dropna(how="all")
fig, ax = plt.subplots(figsize=(9, 4.2)); ax2 = ax.twinx()
ax.plot(c.index, c.truck_emp_k, color=NAVY, lw=2, label="Truck transportation employees (thousands)")
ax2.plot(c.index, c.new_carriers_total, color=ORANGE, lw=1.6, label="New active carriers added per month")
ax.set_ylabel("Employees (thousands)", color=NAVY); ax2.set_ylabel("New carriers per month", color=ORANGE); ax2.spines["right"].set_visible(True)
ax.set_title("Capacity signals disagree since 2023: payrolls shrank while new carrier registrations rose")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(out / "04_capacity_signals.png", dpi=160); plt.close(fig)

# 5. Planning estimate
pe = R["planning_estimate"]; hist = df.ppi_trucking_gf.dropna().loc["2025-09":]
fig, ax = plt.subplots(figsize=(8.5, 4.2)); ax.plot(hist.index, hist.values, color=NAVY, lw=2, label="Published (through Aug 2026)")
mths = [pd.Timestamp(m["month"] + "-01") for m in pe["months"]]; est = [m["ppi_index_estimate"] for m in pe["months"]]
lo = [m["approx_95pct_range"][0] for m in pe["months"]]; hi = [m["approx_95pct_range"][1] for m in pe["months"]]
ax.plot([hist.index[-1]] + mths, [hist.iloc[-1]] + est, color=ORANGE, lw=2, ls="--", marker="o", ms=4, label="Model estimate (diesel held at latest price)")
ax.fill_between([hist.index[-1]] + mths, [hist.iloc[-1]] + lo, [hist.iloc[-1]] + hi, color=ORANGE, alpha=.15, label="Approx. 95% range")
ax.set_ylabel("Trucking price index (PPI)"); ax.set_title("What the September diesel jump implies for trucking prices not yet published")
ax.title.set_fontsize(10.5); ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.text(0.01, 0.01, "Sep and Oct use actual diesel prices (Oct is two weeks in); Nov assumes diesel stays flat. Model estimate, not a guarantee.", fontsize=7, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out / "05_planning_estimate.png", dpi=160); plt.close(fig)

# Tableau extracts (flat, one grain each)
panel = pd.read_sql("select * from panel_monthly", con); panel.to_csv(out / "tableau_monthly_panel.csv", index=False)
d.reset_index().rename(columns={"index": "month"}).to_csv(out / "tableau_monthly_changes.csv", index=False)
t.to_csv(out / "tableau_model_test.csv", index=False)
pd.DataFrame(pe["months"]).assign(low=lo, high=hi).drop(columns="approx_95pct_range").to_csv(out / "tableau_planning_estimate.csv", index=False)
pd.DataFrame(R["shock_events"]).assign(model_predicted_3m_pct=R["shock_predicted_3m_pct"]).to_csv(out / "tableau_shock_events.csv", index=False)
print("outputs:", sorted(p.name for p in out.iterdir()))
