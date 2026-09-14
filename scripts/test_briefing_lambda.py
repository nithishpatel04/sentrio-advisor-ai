import importlib.util
import json
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parents[1]
module_path = project_root / "briefing-service" / "lambda_function.py"
sys.path.insert(0, str(module_path.parent))
spec = importlib.util.spec_from_file_location("briefing_lambda", module_path)
briefing_lambda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(briefing_lambda)


def mock_generate_briefing(ai_evidence):
    return {
        "executive_summary": [],
        "client_household_overview": [],
        "key_changes_since_last_meeting": [],
        "risks_attention": [],
        "recommended_discussion_topics": [],
        "open_actions_followups": [],
        "data_gaps_uncertainty": [],
        "citations": [],
    }


briefing_lambda.generate_briefing = mock_generate_briefing

crm_evidence = {
    "household_external_id": "HH-0001",
    "household_name": "Fowler Household",
    "contacts": [
        {
            "client_external_id": "CL-00001",
            "first_name": "Anthony",
            "last_name": "Fowler",
        }
    ],
    "cases": [],
    "opportunities": [],
    "tasks": [],
    "events": [
        {
            "subject": "Annual Review Meeting",
            "start_datetime": "2025-10-10T10:00:00",
        },
        {
            "subject": "Portfolio Review",
            "start_datetime": "2026-06-15T10:00:00",
        },
        {
            "subject": "Upcoming Annual Review",
            "start_datetime": "2026-10-20T10:00:00",
        },
    ],
}

event = {"body": json.dumps(crm_evidence)}
response = briefing_lambda.lambda_handler(event, None)

print("statusCode:", response["statusCode"])
print(json.dumps(json.loads(response["body"]), indent=2))