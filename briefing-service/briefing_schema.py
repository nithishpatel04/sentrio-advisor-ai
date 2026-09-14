BRIEFING_SCHEMA = {
    "executive_summary": [],
    "client_household_overview": [],
    "key_changes_since_last_meeting": [],
    "risks_attention": [],
    "recommended_discussion_topics": [],
    "open_actions_followups": [],
    "data_gaps_uncertainty": [],
    "citations": [],
}


def validate_briefing_shape(briefing):
    return isinstance(briefing, dict) and set(briefing) == set(BRIEFING_SCHEMA)