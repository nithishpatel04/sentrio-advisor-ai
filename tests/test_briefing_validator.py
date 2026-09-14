import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "briefing-service"))

from briefing_validator import BriefingValidationError, validate_briefing


SECTIONS = [
    "executive_summary",
    "client_household_overview",
    "key_changes_since_last_meeting",
    "risks_attention",
    "recommended_discussion_topics",
    "open_actions_followups",
    "data_gaps_uncertainty",
    "citations",
]


def empty_briefing():
    return {section: [] for section in SECTIONS}


def evidence():
    return {
        "household": {"household_external_id": "HH-0001"},
        "clients": [{"client_external_id": "CL-00001"}],
        "service_requests": {"items": [{"service_request_external_id": "SR-00001"}]},
        "opportunities": {"items": [{"opportunity_external_id": "OPP-00001"}]},
        "tasks": {"items": [{"activity_external_id": "TASK-00001"}]},
        "portfolio": {"accounts": [{"portfolio_account_id": "PA-00001"}]},
        "trading": {"transactions": [{"Transaction_ID": "TXN-000001"}]},
        "attention_items": [{"type": "STALE_RISK_REVIEW"}],
        "data_quality_flags": [{"code": "MISSING_RISK_REVIEW_DATE"}],
    }


def citation(source_type, source_id):
    return {
        "section": "executive_summary",
        "statement": "Supported statement.",
        "source_type": source_type,
        "source_ids": [source_id],
    }


class BriefingValidatorTests(unittest.TestCase):
    def assert_invalid(self, briefing):
        with self.assertRaises(BriefingValidationError):
            validate_briefing(briefing, evidence())

    def test_valid_briefing_passes(self):
        briefing = empty_briefing()
        briefing["citations"] = [citation("CRM", "HH-0001")]
        self.assertIs(validate_briefing(briefing, evidence()), briefing)

    def test_missing_section_fails(self):
        briefing = empty_briefing()
        del briefing["citations"]
        self.assert_invalid(briefing)

    def test_unexpected_top_level_section_fails(self):
        briefing = empty_briefing()
        briefing["extra"] = []
        self.assert_invalid(briefing)

    def test_wrong_section_type_fails(self):
        briefing = empty_briefing()
        briefing["executive_summary"] = {}
        self.assert_invalid(briefing)

    def test_citations_not_list_fails(self):
        briefing = empty_briefing()
        briefing["citations"] = {}
        self.assert_invalid(briefing)

    def test_malformed_citation_fails(self):
        briefing = empty_briefing()
        briefing["citations"] = [{"section": "executive_summary"}]
        self.assert_invalid(briefing)

    def test_unsupported_source_type_fails(self):
        briefing = empty_briefing()
        briefing["citations"] = [citation("INVENTED", "HH-0001")]
        self.assert_invalid(briefing)

    def test_nonexistent_source_id_fails(self):
        briefing = empty_briefing()
        briefing["citations"] = [citation("CRM", "ABC-99999")]
        self.assert_invalid(briefing)

    def test_valid_source_types_and_ids_pass(self):
        briefing = empty_briefing()
        briefing["citations"] = [
            citation("CRM", "CL-00001"),
            citation("PORTFOLIO", "PA-00001"),
            citation("TRADING", "TXN-000001"),
            citation("RULE", "STALE_RISK_REVIEW"),
        ]
        validate_briefing(briefing, evidence())

    def test_invalid_rule_identifier_fails(self):
        briefing = empty_briefing()
        briefing["citations"] = [citation("RULE", "UNSUPPORTED_RULE")]
        self.assert_invalid(briefing)


if __name__ == "__main__":
    unittest.main()