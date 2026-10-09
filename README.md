# Phase 8: Enterprise Financial Crime Command Center

Copy `streamlit_app/` into the project root as `streamlit_app/`. Copy `docs/POWER_BI_POSTGRES.md` into your project docs. Existing `scripts/build_analytics.py` and analytics views must exist.

## Windows PowerShell

```powershell
# From C:\Aditya Project\Project 1\financial-crime-intelligence
# Confirm Docker PostgreSQL is running and Phase 8 analytics views deployed.
venv\Scripts\python.exe -m pip install -r requirements-phase8.txt
$env:PGHOST='127.0.0.1'
$env:PGPORT='55432'
$env:PGDATABASE='aml_analytics'
$env:PGUSER='aml_user'
$env:PGPASSWORD='YOUR_LOCAL_DB_PASSWORD'
venv\Scripts\python.exe -m streamlit run streamlit_app/app.py
```

If your project `.env` already provides `DATABASE_URL`, set `$env:DATABASE_URL` to that SQLAlchemy PostgreSQL URL instead of PG* vars. This app intentionally does not auto-load `.env`; avoid accidentally using the wrong connection. App opens at `http://localhost:8501`.

## Requirements

Pinned versions in `requirements-phase8.txt` are a tested-style baseline for Python 3.12, but check conflicts against existing project pins before installing. Never overwrite your existing `requirements.txt` blindly.

## Caveats

- This is a local development and analyst prototype. Enterprise production deployment also requires SSO/RBAC, audit logs, secrets management, TLS, request limits, alert-status mutation controls, monitoring, and security review.
- App is read-only; all filtering uses parameterized SQL.
- PostgreSQL views are required and should be validated before running Streamlit.
- Cache TTL is 180 seconds. For truly live data, reduce TTL or refresh cache.
