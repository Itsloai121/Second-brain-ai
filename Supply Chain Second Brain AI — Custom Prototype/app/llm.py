import re
from collections import defaultdict

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _target_items(question, operational):
    """Return explicitly named SKUs/products, otherwise the full set."""
    q = question.lower()
    matches = [
        item
        for item in operational
        if item["sku"].lower() in q or item["name"].lower() in q
    ]
    return matches or operational


def _status(item):
    rec = item.get("recommendation")
    return rec["priority"].upper() if rec else "HEALTHY"


def _inventory_report(items):
    lines = ["INVENTORY STATUS", f"Products reviewed: {len(items)}", ""]
    for item in sorted(items, key=lambda x: x["days_of_cover"]):
        lines.extend(
            [
                f"• {item['sku']} — {item['name']}",
                f"  Available: {item['available']:,} units | Allocated: {item['allocated']:,} | In transit: {item['in_transit']:,}",
                f"  Coverage: {item['days_of_cover']} days | Status: {_status(item)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _risk_report(items):
    risks = [x for x in items if x.get("recommendation")]
    risks.sort(key=lambda x: (PRIORITY_ORDER.get(x["recommendation"]["priority"], 9), x["days_of_cover"]))
    if not risks:
        return "INVENTORY RISK REPORT\n\nNo active stock or supplier risk was detected."
    lines = ["INVENTORY RISK REPORT", f"Active risks: {len(risks)}", ""]
    for item in risks:
        rec = item["recommendation"]
        reason = rec["rationale"]
        gap = max(0, reason.get("reorder_point", 0) - reason.get("inventory_position", 0))
        lines.extend(
            [
                f"• [{rec['priority'].upper()}] {item['sku']} — {item['name']}",
                f"  Coverage: {item['days_of_cover']} days vs. {item['lead_days']} lead-time days",
                f"  Inventory position: {reason.get('inventory_position', 0):,} | Reorder point: {reason.get('reorder_point', 0):,}",
                f"  Gap to reorder point: {gap:,} units",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _reorder_report(items):
    rows = [x for x in items if x.get("recommendation", {}).get("type") == "reorder"]
    if not rows:
        return "REORDER PLAN\n\nNo SKU currently meets the reorder trigger."
    lines = ["REORDER PLAN", f"Recommended orders: {len(rows)}", ""]
    for item in sorted(rows, key=lambda x: x["days_of_cover"]):
        rec = item["recommendation"]
        why = rec["rationale"]
        lines.extend(
            [
                f"• {item['sku']} — {item['name']}",
                f"  Recommended quantity: {rec['quantity']:,} units",
                f"  Supplier: {item['supplier_name']} ({item['supplier_code']})",
                f"  Why: {why['days_of_cover']} days of cover; reorder point {why['reorder_point']:,}; inventory position {why['inventory_position']:,}",
                f"  Priority: {rec['priority'].upper()} | Approval: REQUIRED",
                "",
            ]
        )
    lines.append("Next step: review quantities and create a purchase-order draft. Nothing has been sent.")
    return "\n".join(lines)


def _purchase_report(items):
    rows = [x for x in items if x.get("recommendation", {}).get("type") == "reorder"]
    if not rows:
        return "PURCHASE PLAN\n\nNo purchase is currently recommended."
    total = sum(x["recommendation"]["quantity"] * x["unit_cost"] for x in rows)
    lines = ["PURCHASE PLAN", f"Estimated total: ${total:,.2f}", ""]
    grouped = defaultdict(list)
    for item in rows:
        grouped[(item["supplier_code"], item["supplier_name"])].append(item)
    for (code, name), supplier_items in grouped.items():
        subtotal = sum(x["recommendation"]["quantity"] * x["unit_cost"] for x in supplier_items)
        lines.append(f"{name} ({code}) — ${subtotal:,.2f}")
        for item in supplier_items:
            quantity = item["recommendation"]["quantity"]
            lines.append(f"• {item['sku']}: {quantity:,} units × ${item['unit_cost']:,.2f}")
        lines.append("")
    lines.extend(["CONTROL", "All orders remain drafts until the required employee approvals are completed."])
    return "\n".join(lines).rstrip()


def _supplier_report(items):
    suppliers = {}
    for item in items:
        key = item["supplier_code"]
        suppliers[key] = item
    lines = ["SUPPLIER LEAD-TIME REPORT", f"Suppliers reviewed: {len(suppliers)}", ""]
    for item in sorted(suppliers.values(), key=lambda x: x["actual_lead_days"] - x["quoted_lead_days"], reverse=True):
        variance = item["actual_lead_days"] - item["quoted_lead_days"]
        status = "LATE" if variance > 0 else "ON PLAN"
        lines.extend(
            [
                f"• {item['supplier_name']} ({item['supplier_code']})",
                f"  Quoted: {item['quoted_lead_days']} days | Actual: {item['actual_lead_days']} days",
                f"  Variance: {variance:+} days | Status: {status}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _logistics_report(items):
    moving = [x for x in items if x["in_transit"] > 0]
    lines = ["LOGISTICS / IN-TRANSIT STATUS", f"SKUs currently in transit: {len(moving)}", ""]
    if not moving:
        lines.append("No inbound units are currently recorded.")
    else:
        for item in moving:
            lines.extend(
                [
                    f"• {item['sku']} — {item['name']}",
                    f"  In transit: {item['in_transit']:,} units",
                    f"  Supplier: {item['supplier_name']} | Current lead time: {item['actual_lead_days']} days",
                    "",
                ]
            )
    lines.append("Note: the demo data does not include carrier milestones or a confirmed ETA.")
    return "\n".join(lines).rstrip()


def _forecast_report(items):
    lines = ["30-DAY DEMAND FORECAST", f"Products forecast: {len(items)}", ""]
    for item in sorted(items, key=lambda x: x["forecast_30_units"], reverse=True):
        projected_end = item["available"] + item["in_transit"] - item["forecast_30_units"]
        position = "shortfall" if projected_end < 0 else "projected balance"
        lines.extend(
            [
                f"• {item['sku']} — {item['name']}",
                f"  Forecast demand: {item['forecast_30_units']:,} units",
                f"  Recent daily average: {item['avg_daily_demand']:.1f} units",
                f"  {position.title()}: {abs(projected_end):,} units",
                "",
            ]
        )
    lines.append("Method: 28-day trend plus weekday seasonality. Confidence: baseline/demo model.")
    return "\n".join(lines)


def _sku_detail(item):
    rec = item.get("recommendation")
    lines = [f"SKU DETAIL — {item['sku']}", item["name"], "", "INVENTORY"]
    lines.extend(
        [
            f"Available: {item['available']:,} units",
            f"Allocated: {item['allocated']:,} units",
            f"In transit: {item['in_transit']:,} units",
            f"Coverage: {item['days_of_cover']} days",
            "",
            "SUPPLY",
            f"Supplier: {item['supplier_name']} ({item['supplier_code']})",
            f"Lead time: {item['actual_lead_days']} actual vs. {item['quoted_lead_days']} quoted days",
            "",
            "FORECAST",
            f"Next 30 days: {item['forecast_30_units']:,} units",
            "",
            "RECOMMENDATION",
        ]
    )
    if rec:
        lines.append(f"{rec['type'].replace('_', ' ').title()} — {rec['priority'].upper()}")
        if rec.get("quantity"):
            lines.append(f"Suggested quantity: {rec['quantity']:,} units")
    else:
        lines.append("No action currently recommended.")
    return "\n".join(lines)


def _help():
    return """SUPPORTED COMMANDS

• inventory status — available, allocated, in-transit, and coverage
• stock risk — critical SKUs and the reason each is at risk
• reorder plan — recommended quantities and rationale
• purchase plan — quantities grouped by supplier and estimated cost
• demand forecast — 30-day demand projection
• supplier lead times — quoted versus actual lead time
• logistics status — inbound inventory
• NH-HOME-01 details — complete view of one SKU
• approval policy — retrieve the company policy
• seasonal launch playbook — retrieve launch guidance

You can include a SKU or full product name to narrow a report."""


def deterministic_answer(question, context, operational):
    q = " ".join(question.lower().split())
    targets = _target_items(q, operational)
    explicit_targets = targets is not operational

    if re.search(r"\b(hi|hello|hey)\b", q):
        return "Hello. I’m the Navohaus Supply Chain Second Brain.\n\nType “help” to see the reports I can run."
    if q in {"help", "commands", "menu"} or "what can you do" in q:
        return _help()
    if context and any(term in q for term in ["policy", "playbook", "procedure", "guideline", "supplier note"]):
        lines = ["COMPANY KNOWLEDGE", ""]
        for doc in context:
            lines.extend([doc["title"].upper(), doc["body"], f"Source: {doc['source']}", ""])
        return "\n".join(lines).rstrip()
    if "forecast" in q or "demand" in q:
        return _forecast_report(targets)
    if any(term in q for term in ["supplier", "lead time", "lead-time", "late"]):
        return _supplier_report(targets)
    if any(term in q for term in ["logistics", "shipment", "in transit", "inbound", "arriving"]):
        return _logistics_report(targets)
    if any(term in q for term in ["reorder", "re-order"]):
        return _reorder_report(targets)
    if any(term in q for term in ["purchase plan", "buy", "what should we purchase", "order plan"]):
        return _purchase_report(targets)
    if any(term in q for term in ["risk", "stockout", "critical", "running out"]):
        return _risk_report(targets)
    if any(term in q for term in ["inventory", "stock", "on hand", "available"]):
        return _inventory_report(targets)
    if explicit_targets and len(targets) == 1:
        return _sku_detail(targets[0])
    if context:
        lines = ["RELEVANT COMPANY KNOWLEDGE", ""]
        for doc in context:
            lines.extend([doc["title"].upper(), doc["body"], f"Source: {doc['source']}", ""])
        return "\n".join(lines).rstrip()
    return "I could not match that request to a supported report.\n\nType “help” to see the available commands."


async def answer(question, context, operational):
    if LLM_BASE_URL and LLM_API_KEY and LLM_MODEL:
        import httpx

        prompt = f"""You are Navohaus Supply Chain Second Brain. Answer only from supplied context and operational data. Separate facts from recommendations. Never claim an action was executed.
CONTEXT:{context}
OPERATIONS:{operational}
QUESTION:{question}"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    return deterministic_answer(question, context, operational)
