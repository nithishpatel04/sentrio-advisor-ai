import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "briefing-service"))

from rules import analyze_evidence, analyze_risk_review, analyze_tasks


class BriefingRulesTests(unittest.TestCase):
    def test_current_risk_review(self):
        today = date.today()
        result = analyze_risk_review("Balanced", today.isoformat(), today)
        self.assertEqual(result["status"], "CURRENT")

    def test_stale_risk_review(self):
        today = date.today()
        reviewed = (today - timedelta(days=366)).isoformat()
        result = analyze_risk_review("Balanced", reviewed, today)
        self.assertEqual(result["status"], "STALE")

    def test_missing_risk_review(self):
        result = analyze_evidence({"crm": {}})
        self.assertEqual(result["risk_review"]["status"], "UNKNOWN")
        self.assertIn("MISSING_RISK_REVIEW_DATE", self._flag_codes(result))

    def test_cases_and_high_priority_open_case(self):
        result = analyze_evidence({
            "crm": {"cases": [
                {"service_request_external_id": "SR-1", "status": "New", "priority": "High", "subject": "Issue"},
                {"status": "Closed", "priority": "High"},
            ]}
        })
        self.assertEqual(result["service_requests"]["total"], 2)
        self.assertEqual(result["service_requests"]["open"], 1)
        self.assertEqual(result["service_requests"]["high_priority_open"], 1)

    def test_tasks_and_overdue_task(self):
        today = date.today()
        result = analyze_tasks([
            {"subject": "Late", "status": "Open", "activity_date": (today - timedelta(days=1)).isoformat()},
            {"subject": "Done", "status": "Completed", "activity_date": (today - timedelta(days=2)).isoformat()},
        ], today)
        self.assertEqual(result["open"], 1)
        self.assertEqual(result["overdue"], 1)

    def test_opportunities_and_closed_stages(self):
        result = analyze_evidence({
            "crm": {"opportunities": [
                {"name": "Open", "stage": "Proposal"},
                {"name": "Won", "stage": "Closed Won"},
                {"name": "Lost", "stage": "Closed Lost"},
            ]}
        })
        self.assertEqual(result["opportunities"]["total"], 3)
        self.assertEqual(result["opportunities"]["open"], 1)

    def test_portfolio_totals_and_negative_performance(self):
        result = analyze_evidence({
            "portfolio": {"accounts": [
                {"portfolio_account_id": "PA-1", "market_value": "100.10", "performance": {"As_Of_Date": "2026-09-09", "Relative_Performance": "-2.5"}},
                {"portfolio_account_id": "PA-2", "market_value": "200.20", "performance": {"As_Of_Date": "2026-09-09", "Relative_Performance": "1.0"}},
            ]}
        })
        self.assertEqual(result["portfolio"]["total_market_value"], "300.30")
        self.assertEqual(result["portfolio"]["underperforming_accounts"][0]["portfolio_account_id"], "PA-1")

    def test_buy_sell_counts_and_amounts(self):
        result = analyze_evidence({
            "changes_since_last_meeting": {"transactions": [
                {"transaction_id": "TX-1", "transaction_type": "BUY", "total_amount": "10.10"},
                {"transaction_id": "TX-2", "transaction_type": "SELL", "total_amount": "5.05"},
                {"transaction_id": "TX-3", "transaction_type": "BUY", "total_amount": "2.25"},
            ]}
        })
        self.assertEqual(result["trading"]["buy_transactions"], 2)
        self.assertEqual(result["trading"]["sell_transactions"], 1)
        self.assertEqual(result["trading"]["total_buy_amount"], "12.35")
        self.assertEqual(result["trading"]["total_sell_amount"], "5.05")

    def test_missing_meeting_and_no_transactions(self):
        result = analyze_evidence({})
        self.assertIsNone(result["meeting"]["days_since_last_meeting"])
        self.assertIn("NO_PREVIOUS_MEETING", self._flag_codes(result))
        self.assertIn("NO_TRANSACTIONS_SINCE_LAST_MEETING", self._flag_codes(result))

    def test_portfolio_date_conflict_and_missing_performance(self):
        result = analyze_evidence({
            "portfolio": {"accounts": [
                {"portfolio_account_id": "PA-1", "market_value": "1", "performance": {"As_Of_Date": "2026-09-08"}},
                {"portfolio_account_id": "PA-2", "market_value": "2", "performance": {"As_Of_Date": "2026-09-09"}},
                {"portfolio_account_id": "PA-3", "market_value": "3", "performance": {}},
            ]}
        })
        self.assertTrue(result["portfolio"]["portfolio_date_conflict"])
        self.assertIn("PORTFOLIO_DATE_CONFLICT", self._flag_codes(result))
        self.assertIn("MISSING_PORTFOLIO_PERFORMANCE", self._flag_codes(result))

    def test_empty_portfolio_accounts(self):
        result = analyze_evidence({"portfolio": {"accounts": []}})
        self.assertEqual(result["portfolio"]["account_count"], 0)
        self.assertIn("NO_PORTFOLIO_ACCOUNTS", self._flag_codes(result))

    def test_invalid_and_missing_dates_do_not_crash(self):
        result = analyze_evidence({
            "reference_dates": {"last_meeting_date": "not-a-date"},
            "crm": {"tasks": [{"status": "Open", "activity_date": "bad-date"}], "events": [{"start_datetime": None}]},
            "portfolio": {"accounts": [{"market_value": "bad", "performance": {"As_Of_Date": "bad"}}]},
        })
        self.assertIsNone(result["meeting"]["days_since_last_meeting"])
        self.assertEqual(result["tasks"]["overdue"], 0)

    @staticmethod
    def _flag_codes(result):
        return {flag["code"] for flag in result["data_quality_flags"]}


if __name__ == "__main__":
    unittest.main()