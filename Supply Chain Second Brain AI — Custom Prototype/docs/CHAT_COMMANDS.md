# Chat command guide

The deterministic chat mode now routes each command to a separate supply-chain function and returns a structured plain-text report.

| Command | Function |
|---|---|
| `help` | Lists supported reports |
| `inventory status` | Available, allocated, in-transit, and days of cover |
| `stock risk` | Critical SKUs and the evidence behind each risk |
| `reorder plan` | Recommended quantities, suppliers, and rationale |
| `purchase plan` | Recommended orders grouped by supplier with estimated cost |
| `demand forecast` | 30-day demand forecast and projected balance/shortfall |
| `supplier lead times` | Quoted versus actual lead times and variance |
| `logistics status` | Recorded inbound units and supplier context |
| `NH-HOME-01 details` | Full report for one SKU |
| `approval policy` | Retrieves the approval policy |
| `seasonal launch playbook` | Retrieves launch guidance |

A SKU or complete product name can narrow most reports, for example:

```text
forecast NH-TRVL-02
inventory for Arc Storage Tray
reorder NH-HOME-01
```

## Apply the update with Docker

From the project folder:

```powershell
docker compose down
docker compose up --build --force-recreate
```

No database reset is required when upgrading from the previous fixed package. Add `-v` only when you intentionally want to erase and recreate the demo database.
