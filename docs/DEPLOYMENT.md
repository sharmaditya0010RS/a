# Financial Crime Intelligence - Deployment Guide

## Technology
- Python 3.12
- Streamlit
- PostgreSQL 16
- Docker
- SQLAlchemy
- GitHub Actions

## Existing Deployment

Database container: fci_postgres
Dashboard container: fci_dashboard_phase10
Docker network: fci_network

Dashboard URL:
http://127.0.0.1:8502

Database endpoint inside Docker:
fci_postgres:5432

## Start

Run from PowerShell:

    docker start fci_postgres
    docker start fci_dashboard_phase10

## Verify

    docker inspect --format "{{.State.Health.Status}}" fci_dashboard_phase10

    venv\Scripts\python.exe -m scripts.healthcheck

    venv\Scripts\ruff.exe check scripts streamlit_app tests

    venv\Scripts\python.exe -m pytest -q

## Database

The dashboard connects to the existing populated
PostgreSQL database named aml_analytics.

The warehouse contains synthetic transaction data.

Do not remove the existing PostgreSQL container
or delete its database volume.

## Security

- Never commit .env or credentials.
- Keep PostgreSQL ports restricted to localhost.
- Use synthetic data for portfolio demonstrations.
- Do not commit generated investigation reports.

## Analytical Limitations

- Risk scores are heuristic indicators.
- Investigation priority is not proof of wrongdoing.
- Cross-currency amounts are not FX-normalized.
- Generated reports are not immutable evidence records.
