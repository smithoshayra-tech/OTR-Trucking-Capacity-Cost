"""Analysis: fuel pass-through, lead-lag, out-of-time nowcast test, capacity test, spot validation, shock events.
All numbers printed here feed docs/FINDINGS.md. Nothing is hard-coded."""
import sqlite3, json, pathlib, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
warnings.filterwarnings("ignore")
root = pathlib.Path(__file__).resolve().parents[1]
con = sqlite3.connect(root / "data/processed/otr.db")
df = pd.read_sql("select * from features_monthly", con, parse_dates=["month"]).set_index("month")
df["diesel_mom"] = 100 * df.diesel_usd_gal.pct_change()
df["ppi_mom"] = df.ppi_trk_mom
df["emp_mom"] = 100 * df.truck_emp_k.pct_change()
df["tsi_mom"] = 100 * df.tsi_freight.pct_change()
df["fpt_mom"] = 100 * df.freight_per_trucker.pct_change()
R = {}

# 1. Stationarity: why YoY correlations are not trusted
R["adf_p"] = {c: round(adfuller(df[c].dropna(), autolag="AIC")[1], 3)
              for c in ["ppi_trucking_gf", "ppi_trk_yoy", "diesel_yoy", "ppi_mom", "diesel_mom"]}
d = df[["ppi_trk_yoy", "diesel_yoy"]].dropna()
R["yoy_corr"] = round(d.corr().iloc[0, 1], 3)

# 2. Pass-through (month-over-month, stationary): distributed lag with HAC errors
L = 3
X = pd.concat({f"diesel_l{l}": df.diesel_mom.shift(l) for l in range(L)}, axis=1)
dd = pd.concat([df.ppi_mom, X], axis=1).dropna()
m = sm.OLS(dd.ppi_mom, sm.add_constant(dd.drop(columns="ppi_mom"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
ci = m.conf_int()
R["passthrough"] = {"coef": m.params.round(4).to_dict(), "p": m.pvalues.round(4).to_dict(),
                    "sum_lags": round(m.params[1:].sum(), 4), "r2": round(m.rsquared, 3), "n": int(m.nobs)}
# CI on the sum of lags
w = np.zeros(len(m.params)); w[1:] = 1
se = float(np.sqrt(w @ m.cov_params().values @ w)); s = float(w @ m.params.values)
R["passthrough"]["sum_ci95"] = [round(s - 1.96 * se, 4), round(s + 1.96 * se, 4)]
# sub-period stability
sub = {}
for a, b in [("2019-04", "2021-12"), ("2022-01", "2023-12"), ("2024-01", "2026-08")]:
    t = dd.loc[a:b]
    mm = sm.OLS(t.ppi_mom, sm.add_constant(t.drop(columns="ppi_mom").sum(axis=1).rename("sum_diesel"))).fit()
    sub[f"{a}..{b}"] = {"n": len(t), "slope": round(mm.params["sum_diesel"], 3), "r2": round(mm.rsquared, 3)}
R["passthrough_subperiods"] = sub

# 3. Out-of-time test of a planning nowcast: train 2019-04..2023-12, test 2024-01..2026-08
def feats(kind):
    cols = {"naive": [], "fuel": ["diesel_mom", "d1", "d2"],
            "fuel_capacity": ["diesel_mom", "d1", "d2", "emp_mom_l1", "fpt_mom_l1", "tsi_mom_l1"]}[kind]
    return cols
F = df.copy()
F["d1"] = F.diesel_mom.shift(1); F["d2"] = F.diesel_mom.shift(2)
F["emp_mom_l1"] = F.emp_mom.shift(1); F["fpt_mom_l1"] = F.fpt_mom.shift(1); F["tsi_mom_l1"] = F.tsi_mom.shift(1)
oos = {}
for h in [0, 1, 3]:
    F[f"y{h}"] = F.ppi_mom.shift(-h)
    rows = {}
    for kind in ["naive", "fuel", "fuel_capacity"]:
        cols = feats(kind)
        need = cols + [f"y{h}"]
        data = F[need].dropna()
        preds, acts = [], []
        for t in data.loc["2024-01":].index:
            train = data.loc[:t - pd.DateOffset(months=h + 1)] if h else data.loc[:t - pd.DateOffset(months=1)]
            if kind == "naive":
                p = train[f"y{h}"].mean()
            else:
                mod = sm.OLS(train[f"y{h}"], sm.add_constant(train[cols])).fit()
                p = float(mod.predict(sm.add_constant(data.loc[[t], cols], has_constant="add")).iloc[0])
            preds.append(p); acts.append(data.loc[t, f"y{h}"])
        e = np.array(acts) - np.array(preds)
        rows[kind] = {"n": len(e), "mae": round(float(np.mean(np.abs(e))), 3), "rmse": round(float(np.sqrt(np.mean(e ** 2))), 3)}
    for k in ["fuel", "fuel_capacity"]:
        rows[k]["rmse_gain_vs_naive_pct"] = round(100 * (1 - rows[k]["rmse"] / rows["naive"]["rmse"]), 1)
    oos[f"h{h}"] = rows
R["oos_expanding_window"] = oos

# 4. Does capacity add anything in-sample beyond fuel? (nested F test)
cols_f = ["diesel_mom", "d1", "d2"]; cols_c = cols_f + ["emp_mom_l1", "fpt_mom_l1", "tsi_mom_l1"]
dat = F[["ppi_mom"] + cols_c].dropna()
a = sm.OLS(dat.ppi_mom, sm.add_constant(dat[cols_f])).fit(); b = sm.OLS(dat.ppi_mom, sm.add_constant(dat[cols_c])).fit()
fs = b.compare_f_test(a)
R["capacity_nested_F"] = {"F": round(fs[0], 2), "p": round(fs[1], 3), "r2_fuel": round(a.rsquared, 3), "r2_fuel_capacity": round(b.rsquared, 3), "n": int(b.nobs)}

# 5. Validation of the price proxy against DAT spot rates (2019-01..2024-05)
sp = df[["spot_dry_van", "ppi_trucking_gf"]].dropna()
R["spot_validation"] = {"n_months": len(sp),
    "corr_levels": round(sp.corr().iloc[0, 1], 3),
    "corr_mom": round(sp.pct_change().dropna().corr().iloc[0, 1], 3),
    "corr_yoy": round(sp.pct_change(12).dropna().corr().iloc[0, 1], 3)}

# 6. Shock events: diesel up >15% in a month. PPI change measured from the month BEFORE the shock
#    through the shock month +1 and +3, compared with the pass-through model's prediction
ev = df[df.diesel_mom > 15].copy()
rows = []
for t in ev.index:
    pos = df.index.get_loc(t)
    ppi0 = df.ppi_trucking_gf.iloc[pos - 1]
    out = {"month": t.strftime("%Y-%m"), "diesel_mom_pct": round(df.diesel_mom.iloc[pos], 1)}
    for k in [1, 3]:
        if pos + k < len(df): out[f"ppi_change_to_t_plus_{k}_pct"] = round(100 * (df.ppi_trucking_gf.iloc[pos + k] / ppi0 - 1), 2)
    rows.append(out)
R["shock_events"] = rows
pred_per_pct = R["passthrough"]["sum_lags"]
R["shock_predicted_3m_pct"] = [round(pred_per_pct * r["diesel_mom_pct"], 2) for r in rows]

# 7. Capacity context (descriptive only)
cap = df[["truck_emp_k", "new_carriers_total", "new_carriers_forhire", "tsi_freight", "freight_per_trucker"]]
peak = cap.truck_emp_k.idxmax()
R["capacity"] = {"truck_emp_peak_month": peak.strftime("%Y-%m"), "truck_emp_peak_k": float(cap.truck_emp_k.max()),
    "truck_emp_latest_month": cap.truck_emp_k.dropna().index[-1].strftime("%Y-%m"), "truck_emp_latest_k": float(cap.truck_emp_k.dropna().iloc[-1]),
    "new_carriers_2023_avg": round(float(cap.loc["2023", "new_carriers_total"].mean())), 
    "new_carriers_2025_avg": round(float(cap.loc["2025", "new_carriers_total"].mean())),
    "freight_per_trucker_2019_avg": round(float(cap.loc["2019", "freight_per_trucker"].mean()), 4),
    "freight_per_trucker_latest": round(float(cap.freight_per_trucker.dropna().iloc[-1]), 4)}

# 8. Planning range for current diesel: expected PPI change over next 3 months per +10% diesel
resid_sd = float(np.std(m.resid, ddof=len(m.params)))
R["scenario_per_10pct_diesel"] = {"expected_ppi_pct_3m": round(10 * R["passthrough"]["sum_lags"], 2),
    "ci95_pct_3m": [round(10 * R["passthrough"]["sum_ci95"][0], 2), round(10 * R["passthrough"]["sum_ci95"][1], 2)],
    "monthly_resid_sd_pct": round(resid_sd, 2)}

# 9. Planning estimate for months not yet in the PPI data (Sep-Nov 2026), using weekly diesel through 2026-10-12
wk = pd.read_sql("select week_start, eia_usd_gal from fact_diesel_weekly", con, parse_dates=["week_start"]).set_index("week_start").eia_usd_gal
mon = wk.groupby(wk.index.to_period("M")).mean()
aug, sep, octo = mon.loc["2026-08"], mon.loc["2026-09"], mon.loc["2026-10"]
last = float(wk.iloc[-1])
path = [("2026-09", sep), ("2026-10", octo), ("2026-11", last)]        # Nov assumes diesel stays at the latest weekly price
dm = [100 * (sep / aug - 1), 100 * (octo / sep - 1), 100 * (last / octo - 1)]
hist = list(df.diesel_mom.dropna().iloc[-2:])                          # Jul, Aug 2026 changes
seq = hist + dm
c = m.params
ppi = float(df.ppi_trucking_gf.dropna().iloc[-1]); ppi0 = ppi; est = []
for i in range(3):
    mom = c["const"] + c["diesel_l0"] * seq[2 + i] + c["diesel_l1"] * seq[1 + i] + c["diesel_l2"] * seq[i]
    ppi *= 1 + mom / 100
    est.append({"month": path[i][0], "diesel_avg_usd_gal": round(float(path[i][1]), 3), "diesel_mom_pct": round(dm[i], 1),
                "model_ppi_mom_pct": round(mom, 2), "ppi_index_estimate": round(ppi, 1),
                "approx_95pct_range": [round(ppi0 * (1 + (ppi / ppi0 - 1) - 1.96 * resid_sd * np.sqrt(i + 1) / 100), 1),
                                       round(ppi0 * (1 + (ppi / ppi0 - 1) + 1.96 * resid_sd * np.sqrt(i + 1) / 100), 1)]})
R["planning_estimate"] = {"last_published_month": "2026-08", "last_published_ppi": round(ppi0, 2),
                          "assumption": "diesel stays at the latest weekly price ($%.3f) through November" % last, "months": est,
                          "cumulative_pct_vs_aug": round(100 * (ppi / ppi0 - 1), 2)}

out = root / "data/processed/results.json"; out.write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=2))
df.reset_index().to_csv(root / "data/processed/features_with_changes.csv", index=False)
