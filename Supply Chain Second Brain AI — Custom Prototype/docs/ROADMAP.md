# 12-step implementation roadmap

| Step | MVP implementation | Production exit criterion |
|---|---|---|
| 1. Company data | Canonical CSV contracts and seeded operating data | Owners, freshness SLAs, and quality rules agreed |
| 2. PostgreSQL | Normalized operational schema and indexes | Managed DB, backups, migrations, least privilege |
| 3. Python backend | FastAPI services and typed endpoints | Auth, background jobs, tracing, CI/CD |
| 4. Calculations | Availability, cover, safety stock, ROP, EOQ | Finance/operations sign-off against samples |
| 5. Forecasting | Trend + weekday seasonal baseline | Backtests beat seasonal-naive baseline |
| 6. Decisions | Explainable reorder and supplier alerts | Thresholds approved by planners |
| 7. Memory | Stored conversation/decision exchanges | Retention, deletion, and privacy policies enforced |
| 8. Retrieval | PostgreSQL full-text knowledge search | Hybrid semantic + lexical retrieval evaluated |
| 9. LLM + tools | Optional OpenAI-compatible adapter | Model risk controls and prompt regression suite |
| 10. Chat | Responsive planning control center | User testing and accessibility pass |
| 11. Actions | Approval-required PO/expedite drafts | ERP/WMS integrations with idempotency and audit |
| 12. Monitoring | Health and metric contract | Alerts, dashboards, drift and cost monitoring |

## Recommended delivery order

- **Weeks 1–2:** source mapping, schema, ingestion, data quality.
- **Weeks 3–4:** inventory/lead-time calculations and baseline forecast.
- **Weeks 5–6:** recommendations, planner review, backtesting.
- **Weeks 7–8:** retrieval, memory, LLM answers, chat interface.
- **Weeks 9–10:** approval workflows, integrations, monitoring, pilot.
