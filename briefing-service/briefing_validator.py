import re

from briefing_schema import BRIEFING_SCHEMA


class BriefingValidationError(Exception):
    """Raised when a generated briefing is unsafe or structurally invalid."""


ALLOWED_SOURCE_TYPES = {"CRM", "PORTFOLIO", "TRADING", "RULE"}
IDENTIFIER_KEYS = {
    "householdexternalid",
    "clientexternalid",
    "servicerequestexternalid",
    "opportunityexternalid",
    "activityexternalid",
    "portfolioaccountid",
    "transactionid",
}


def _normalized_key(key):
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _collect_source_ids(value, source_ids):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = _normalized_key(key)
            if normalized in IDENTIFIER_KEYS and isinstance(item, str) and item:
                source_ids.add(item)
            _collect_source_ids(item, source_ids)
    elif isinstance(value, list):
        for item in value:
            _collect_source_ids(item, source_ids)


def _collect_rule_ids(ai_evidence):
    rule_ids = set()
    for item in ai_evidence.get("attention_items", []):
        if isinstance(item, dict) and isinstance(item.get("type"), str):
            rule_ids.add(item["type"])
    for item in ai_evidence.get("data_quality_flags", []):
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            rule_ids.add(item["code"])
    return rule_ids


def _invalid(message):
    raise BriefingValidationError(message)


def validate_briefing(briefing, ai_evidence):
    if not isinstance(briefing, dict):
        _invalid("Advisor briefing must be a JSON object.")

    expected_sections = set(BRIEFING_SCHEMA)
    if set(briefing) != expected_sections:
        _invalid("Advisor briefing has an invalid top-level structure.")

    if any(not isinstance(briefing[section], list) for section in expected_sections):
        _invalid("Advisor briefing sections must be arrays.")

    if not isinstance(ai_evidence, dict):
        _invalid("Controlled AI evidence is invalid.")

    source_ids = set()
    _collect_source_ids(ai_evidence, source_ids)
    rule_ids = _collect_rule_ids(ai_evidence)

    for citation in briefing["citations"]:
        if not isinstance(citation, dict):
            _invalid("Advisor briefing contains a malformed citation.")
        required = {"section", "statement", "source_type", "source_ids"}
        if set(citation) != required:
            _invalid("Advisor briefing contains an incomplete citation.")
        if citation["section"] not in expected_sections:
            _invalid("Advisor briefing contains a citation for an invalid section.")
        if not isinstance(citation["statement"], str) or not citation["statement"].strip():
            _invalid("Advisor briefing contains an invalid citation statement.")
        source_type = citation["source_type"]
        if source_type not in ALLOWED_SOURCE_TYPES:
            _invalid("Advisor briefing contains an unsupported citation source type.")
        source_list = citation["source_ids"]
        if not isinstance(source_list, list) or not source_list:
            _invalid("Advisor briefing contains an invalid citation source list.")
        for source_id in source_list:
            if not isinstance(source_id, str):
                _invalid("Advisor briefing contains an invalid citation source ID.")
            valid_ids = rule_ids if source_type == "RULE" else source_ids
            if source_id not in valid_ids:
                _invalid("Advisor briefing contains an unsupported citation source ID.")

    return briefing