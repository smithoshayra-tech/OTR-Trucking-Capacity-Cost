import sqlite3, sys, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
con = sqlite3.connect(root / "data/processed/otr.db")
for f in sys.argv[1:]:
    sql = (root / "sql" / f).read_text()
    if f.startswith("03"):
        for row in con.execute(sql): print(row)
    else:
        con.executescript(sql); con.commit(); print("ran", f)
