import json
import sys
import unittest
from pathlib import Path


briefing_service = Path(__file__).resolve().parents[1] / "briefing-service"
sys.path.insert(0, str(briefing_service))

from ai_input import build_ai_evidence
from briefing_schema import BRIEFING_SCHEMA, validate_briefing_shape
from prompt_builder import build_system_prompt, build_user_prompt


class AIInputTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {
            "household_external_id": "HH-0001",
            "reference_dates": {"last_meeting_date": "2026-06-15"},
            "crm": {
                "household_name": "Fowler Household",
                "risk_profile": "Balanced",
                "risk_profile_last_reviewed": "2025-01-01",
                "contacts": [{
                    "client_external_id": "CL-1",
                    "first_name": "Anthony",
                    "last_name": "Fowler",
                    "title": "Mr.",
                    "email": "private@example.com",
                    "phone": "555-0100",
                }],
                "cases": [{
                    "Service_Request_External_ID": "SR-1",
                    "Subject": "Urgent issue",
                    "Status": "New",
                    "Priority": "High",
                }],
                "opportunities": [{
                    "Opportunity_External_ID": "OP-1",
                    "Name": "Open opportunity",
                    "StageName": "Proposal",
                }],
                "tasks": [{
                    "Activity_External_ID": "ACT-1",
                    "Subject": "Follow up",
                    "Status": "Open",
                    "ActivityDate": "2020-01-01",
                }],
            },
            "portfolio": {"accounts": [{
                "portfolio_account_id": "PA-1",
                "account_type": "Investment",
                "market_value": "100.00",
                "currency": "CAD",
                "performance": {
                    "As_Of_Date": "2026-09-08",
                    "Relative_Performance": "-1.5",
                },
            }]},
            "changes_since_last_meeting": {"transactions": {
                "transactions": [{
                    "Transaction_ID": "TX-1",
                    "Transaction_Date": "2026-06-20",
                    "Transaction_Type": "BUY",
                    "Symbol": "MSFT",
                    "Quantity": "1",
                    "Price": "100",
                    "Total_Amount": "100",
                    "Currency": "CAD",
                }],
            }},
        }

    def test_expected_household_fields_and_minimization(self):
        result = build_ai_evidence(self.evidence)
        self.assertEqual(result["household"]["household_name"], "Fowler Household")
        self.assertEqual(result["household"]["risk_profile"], "Balanced")
        self.assertNotIn("email", result["clients"][0])
        self.assertNotIn("phone", result["clients"][0])

    def test_flags_and_attention_items_are_preserved(self):
        result = build_ai_evidence(self.evidence)
        codes = {flag["code"] for flag in result["data_quality_flags"]}
        attention_types = {item["type"] for item in result["attention_items"]}
        self.assertIn("STALE_RISK_REVIEW", codes)
        self.assertIn("STALE_RISK_REVIEW", attention_types)
        self.assertIn("HIGH_PRIORITY_SERVICE_REQUEST", attention_types)
        self.assertIn("OVERDUE_TASK", attention_types)
        self.assertIn("PORTFOLIO_UNDERPERFORMANCE", attention_types)

    def test_source_ids_are_retained(self):
        result = build_ai_evidence(self.evidence)
        self.assertEqual(result["service_requests"]["items"][0]["service_request_external_id"], "SR-1")
        self.assertEqual(result["opportunities"]["items"][0]["opportunity_external_id"], "OP-1")
        self.assertEqual(result["tasks"]["items"][0]["activity_external_id"], "ACT-1")
        self.assertEqual(result["portfolio"]["accounts"][0]["portfolio_account_id"], "PA-1")
        self.assertEqual(result["trading"]["transactions"][0]["Transaction_ID"], "TX-1")

    def test_portfolio_conflict_attention(self):
        self.evidence["portfolio"]["accounts"].append({
            "portfolio_account_id": "PA-2",
            "market_value": "50",
            "performance": {"As_Of_Date": "2026-09-09"},
        })
        result = build_ai_evidence(self.evidence)
        self.assertIn("PORTFOLIO_DATE_CONFLICT", {item["type"] for item in result["attention_items"]})

    def test_missing_fields_do_not_crash(self):
        result = build_ai_evidence({})
        self.assertEqual(result["clients"], [])
        self.assertEqual(result["portfolio"]["account_count"], 0)
        self.assertEqual(result["trading"]["transactions"], [])

    def test_prompts_are_strings_and_user_prompt_contains_json(self):
        ai_evidence = build_ai_evidence(self.evidence)
        system_prompt = build_system_prompt()
        self.assertIsInstance(system_prompt, str)
        for required_text in (
            "source_type",
            "source_ids",
            "CRM",
            "PORTFOLIO",
            "TRADING",
            "RULE",
            "Do not use source, evidence, reference, references, or source_id",
            "MUST NEVER be returned",
            "Never fabricate a citation",
            "NON-EMPTY JSON array",
            "Claims about the last meeting date",
            "actual CRM Event or Activity external ID",
            "If data_quality_flags is empty",
            "Never invent identifiers such as NO_ISSUES",
            "rebalancing, buying, selling, holding",
            "do not infer suitability",
        ):
            self.assertIn(required_text, system_prompt)
        user_prompt = build_user_prompt(ai_evidence)
        self.assertIsInstance(user_prompt, str)
        self.assertIn('"household"', user_prompt)
        self.assertIn('"executive_summary"', user_prompt)
        self.assertIn("Every citation must contain exactly section, statement, source_type, and source_ids", user_prompt)
        self.assertIn("source_ids must contain at least one actual string ID", user_prompt)
        self.assertIn("Meeting claims must cite the actual Event/Activity ID", user_prompt)
        json.dumps(ai_evidence)

    def test_briefing_schema_sections(self):
        expected = {
            "executive_summary",
            "client_household_overview",
            "key_changes_since_last_meeting",
            "risks_attention",
            "recommended_discussion_topics",
            "open_actions_followups",
            "data_gaps_uncertainty",
            "citations",
        }
        self.assertEqual(set(BRIEFING_SCHEMA), expected)
        self.assertTrue(validate_briefing_shape({key: [] for key in expected}))


if __name__ == "__main__":
    unittest.main()