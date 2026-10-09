# Power BI Desktop → PostgreSQL 16 (live database)

1. Start Docker container `fci_postgres` and verify it exposes `127.0.0.1:55432`.
2. Run `venv\Scripts\python.exe -m scripts.build_analytics` from project root, if analytics views have not been created yet.
3. Open Power BI Desktop → Home → Get data → More → Database → PostgreSQL database.
4. Server: `127.0.0.1:55432`; Database: `aml_analytics`.
5. Choose **Import** initially (recommended for responsive executive reporting), or **DirectQuery** for live SQL-backed queries. Import is a PostgreSQL connection, not CSV, but requires dataset refresh to see new data.
6. Authentication: Database → Username `aml_user`, password from your local `.env` or Docker configuration. Never commit or share it.
7. Navigator → select analytics views: `vw_executive_kpis`, `vw_daily_risk_trends`, `vw_detection_effectiveness`, `vw_entity_risk_leaderboard`, `vw_investigation_queue`. Choose Transform Data.
8. For Import, consider filtering `vw_entity_risk_leaderboard` to HIGH/CRITICAL, and `vw_investigation_queue` to relevant time windows before loading. Do not import 5M fact rows.
9. Set `full_date` to Date, timestamp fields to Date/Time, score/count fields to Whole Number, `amount_paid` to Decimal Number, and IDs to Whole Number or Text as appropriate.
10. Load. Start with independent tables: no relationships are necessary for the summary KPI views. Date slicers on `vw_daily_risk_trends` do not automatically filter all-time summary KPIs.
11. Build four report pages: Executive (cards + daily trend); Investigations (alert table, risk/status slicers); Entity Intelligence (risk leaderboard); Model Performance (precision, recall, F1, confusion matrix).
12. In Power BI Service, a local PostgreSQL Docker database normally requires an **on-premises data gateway** for scheduled refresh/DirectQuery. Configure gateway data source and credentials; desktop localhost alone does not make database available to the cloud service.

## DAX measures

```dax
Alert Rate % = DIVIDE(SUM(vw_executive_kpis[total_alerts]), SUM(vw_executive_kpis[total_transactions]), 0)

Precision % = DIVIDE(SUM(vw_detection_effectiveness[true_positives]), SUM(vw_detection_effectiveness[true_positives]) + SUM(vw_detection_effectiveness[false_positives]), 0)

Recall % = DIVIDE(SUM(vw_detection_effectiveness[true_positives]), SUM(vw_detection_effectiveness[true_positives]) + SUM(vw_detection_effectiveness[false_negatives]), 0)

F1 % = DIVIDE(2 * [Precision %] * [Recall %], [Precision %] + [Recall %], 0)

Open Alerts = CALCULATE(COUNTROWS(vw_investigation_queue), vw_investigation_queue[alert_status] = "OPEN")

Critical Entities = CALCULATE(COUNTROWS(vw_entity_risk_leaderboard), vw_entity_risk_leaderboard[entity_risk_level] = "CRITICAL")
```

Format percentage measures as Percentage. The source `alert_rate_pct` is already 0–100, whereas `Alert Rate %` DAX is 0–1.

## Security and correctness

- Use a read-only reporting DB role in deployed environments; avoid distributing the AML writer credentials.
- Never sum `amount_paid` across different currencies without FX conversion.
- The `is_laundering` column is synthetic ground truth, not a scoring feature.
- These detection metrics evaluate Phase 6 transaction alerts only, not Phase 7 entity scores.
- DirectQuery support and query performance depend on Power BI Desktop, connector, and database configuration.
