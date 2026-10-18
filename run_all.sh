#!/usr/bin/env bash
set -e
python3 src/01_ingest.py
python3 src/02_run_sql.py 02_clean.sql 03_validate.sql 04_features.sql
python3 src/03_analysis.py > /dev/null
python3 src/04_outputs.py
