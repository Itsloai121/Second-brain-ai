# Navohaus Supply Chain Second Brain AI

A runnable MVP for an ~85-person DTC, marketplace, and wholesale consumer-products company.

## What is included

1. Demo company data and CSV templates
2. PostgreSQL schema and seed data
3. FastAPI Python backend
4. Inventory, safety-stock, reorder-point, EOQ, and lead-time calculations
5. Lightweight demand forecasting with trend and seasonal factors
6. Explainable recommendation engine
7. Conversation and decision memory
8. PostgreSQL full-text knowledge retrieval
9. Optional OpenAI-compatible LLM adapter plus deterministic fallback
10. Responsive chat/control-center interface
11. Draft purchase-order and supplier-expedite actions
12. Health, forecast-error, recommendation-acceptance, and audit monitoring

## Quick start

1. Copy environment settings:
   ```bash
   cp .env.example .env
   ```
2. Start the stack:
   ```bash
   docker compose up --build
   ```
3. Open `http://localhost:8000`.
4. API docs are at `http://localhost:8000/docs`.

The seed script creates representative products, suppliers, inventory, sales, purchase orders, and knowledge documents.

## Architecture

```text
Company data -> PostgreSQL -> FastAPI -> calculations -> forecast
             -> recommendations -> memory -> retrieval -> LLM/tools
             -> chat UI -> draft actions -> evaluation/monitoring
```

## Core API routes

- `GET /api/dashboard` — KPIs, risks, and latest recommendations
- `POST /api/forecast/{sku}` — forecast and accuracy estimate
- `POST /api/recommendations/run` — refresh planning recommendations
- `POST /api/chat` — ask supply-chain questions
- `POST /api/actions/purchase-order/draft` — create an approval-required PO draft
- `POST /api/actions/expedite/draft` — create an approval-required expedite request
- `GET /api/monitoring` — service and decision metrics

## Safety model

Actions are drafts only. The MVP never sends a PO or supplier message automatically. A person must review and approve any downstream action.

## Replacing demo data

Use the files in `data/templates/` as import contracts. Keep SKUs and supplier codes stable. In production, load data via scheduled ELT from the storefront, marketplaces, WMS/3PL, ERP/accounting, and wholesale platform.

## Production upgrades

- Replace the simple forecast with hierarchical probabilistic models by SKU/channel.
- Add pgvector for semantic retrieval alongside full-text search.
- Add SSO/RBAC, secrets management, migrations, background jobs, and event-driven integrations.
- Enforce approval thresholds by role and dollar value.
- Add data-quality checks and forecast backtesting by segment.


## Structured chat commands

Version 0.2 routes each static command to its own report instead of returning one shared risk message. Use the quick-report buttons in the interface or type `help`. See `docs/CHAT_COMMANDS.md` for the complete command and function list.


## Control panel additions (v0.3)

- **Clear chat** resets the visible conversation and starts a new local chat session.
- **System check report** validates the PostgreSQL connection, active products and suppliers, inventory values, supplier assignments, sales freshness, and knowledge documents.
- **Employee report** opens a closable dialog and saves employee improvement requests in the existing audited action-draft store.
- **Commands & its-functions** opens a complete command reference.

The dialogs can be closed with the X button, by clicking outside the dialog, or by pressing Escape.
