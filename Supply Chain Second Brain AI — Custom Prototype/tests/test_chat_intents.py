import unittest

from app.llm import deterministic_answer


def sample_operations():
    return [
        {
            "sku": "NH-HOME-01",
            "name": "Arc Storage Tray",
            "on_hand": 420,
            "available": 355,
            "allocated": 65,
            "in_transit": 0,
            "days_of_cover": 5.8,
            "avg_daily_demand": 61.0,
            "actual_lead_days": 36,
            "quoted_lead_days": 32,
            "lead_days": 36,
            "supplier_code": "SUP-ALP",
            "supplier_name": "Alpine Works",
            "unit_cost": 12.5,
            "forecast_30_units": 1830,
            "recommendation": {
                "type": "reorder",
                "priority": "critical",
                "quantity": 1335,
                "rationale": {
                    "inventory_position": 355,
                    "reorder_point": 2256,
                    "avg_daily_demand": 61.0,
                    "days_of_cover": 5.8,
                    "lead_days": 36,
                },
            },
        },
        {
            "sku": "NH-TRVL-02",
            "name": "Fold Travel Organizer",
            "on_hand": 190,
            "available": 110,
            "allocated": 80,
            "in_transit": 500,
            "days_of_cover": 11.7,
            "avg_daily_demand": 52.0,
            "actual_lead_days": 68,
            "quoted_lead_days": 55,
            "lead_days": 68,
            "supplier_code": "SUP-SUN",
            "supplier_name": "Sunfield Manufacturing",
            "unit_cost": 9.4,
            "forecast_30_units": 1560,
            "recommendation": {
                "type": "reorder",
                "priority": "critical",
                "quantity": 1421,
                "rationale": {
                    "inventory_position": 610,
                    "reorder_point": 3618,
                    "avg_daily_demand": 52.0,
                    "days_of_cover": 11.7,
                    "lead_days": 68,
                },
            },
        },
    ]


class TestChatIntents(unittest.TestCase):
    def setUp(self):
        self.ops = sample_operations()

    def answer(self, question, context=None):
        return deterministic_answer(question, context or [], self.ops)

    def test_commands_return_distinct_reports(self):
        reports = {
            self.answer("inventory status").splitlines()[0],
            self.answer("stock risk").splitlines()[0],
            self.answer("reorder plan").splitlines()[0],
            self.answer("purchase plan").splitlines()[0],
            self.answer("demand forecast").splitlines()[0],
            self.answer("supplier lead times").splitlines()[0],
            self.answer("logistics status").splitlines()[0],
        }
        self.assertEqual(len(reports), 7)

    def test_reorder_is_organized_and_has_no_raw_dict(self):
        response = self.answer("reorder plan")
        self.assertIn("REORDER PLAN", response)
        self.assertIn("Recommended quantity: 1,335 units", response)
        self.assertIn("Approval: REQUIRED", response)
        self.assertNotIn("{'", response)

    def test_specific_sku_narrows_inventory(self):
        response = self.answer("inventory for NH-HOME-01")
        self.assertIn("NH-HOME-01", response)
        self.assertNotIn("NH-TRVL-02", response)

    def test_policy_precedes_purchase_trigger(self):
        context = [{"title": "Purchase approval policy", "body": "Finance approval is required.", "source": "Policy"}]
        response = self.answer("What is the purchase approval policy?", context)
        self.assertTrue(response.startswith("COMPANY KNOWLEDGE"))

    def test_help_lists_commands(self):
        response = self.answer("help")
        self.assertIn("SUPPORTED COMMANDS", response)
        self.assertIn("reorder plan", response)


if __name__ == "__main__":
    unittest.main()
