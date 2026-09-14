import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from ai_input import build_ai_evidence
from bedrock_client import BedrockResponseError, generate_briefing
from briefing_validator import BriefingValidationError, validate_briefing
from rules import analyze_evidence


API_BASE_URL = os.getenv(
    "SENTRIO_API_BASE_URL",
    "https://5ty7d7s890.execute-api.us-east-1.amazonaws.com",
).rstrip("/")


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str),
    }


def _parse_body(event):
    """
    Supports:
    1. API Gateway events where payload is inside event["body"]
    2. Direct Lambda test events containing CRM payload directly
    """

    if not isinstance(event, dict):
        raise ValueError("Lambda event must be a JSON object")

    if "body" not in event:
        return event

    body = event.get("body")

    if body is None:
        return {}

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        if not body.strip():
            return {}

        return json.loads(body)

    raise ValueError("Unsupported request body format")


def _parse_datetime(value):
    if not value:
        return None

    try:
        normalized = str(value).strip()

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        parsed = datetime.fromisoformat(normalized)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (ValueError, TypeError):
        return None


def _find_last_meeting(events):
    """
    Deterministically finds the most recent meeting that occurred
    before the current time.

    Future meetings are not considered previous meetings.
    """

    now = datetime.now(timezone.utc)

    latest_event = None
    latest_datetime = None

    for event in events or []:
        if not isinstance(event, dict):
            continue

        start_value = (
            event.get("start_datetime")
            or event.get("StartDateTime")
            or event.get("startDateTime")
        )

        parsed = _parse_datetime(start_value)

        if parsed is None:
            continue

        if parsed >= now:
            continue

        if latest_datetime is None or parsed > latest_datetime:
            latest_datetime = parsed
            latest_event = event

    return latest_event, latest_datetime


def _http_get_json(url):
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            status = response.getcode()
            body = response.read().decode("utf-8")

            if not body:
                return status, {}

            return status, json.loads(body)

    except urllib.error.HTTPError as exc:
        exc.read()

        raise RuntimeError(
            f"HTTP request failed with status {exc.code}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Unable to reach downstream service"
        ) from exc


def _get_portfolio(household_external_id):
    household_id = urllib.parse.quote(
        household_external_id,
        safe="",
    )

    url = (
        f"{API_BASE_URL}"
        f"/households/{household_id}/portfolio"
    )

    print(f"Portfolio URL: {url}")

    status, payload = _http_get_json(url)

    print(f"Portfolio response status: {status}")

    if status < 200 or status >= 300:
        raise RuntimeError(
            f"Portfolio service returned HTTP {status}"
        )

    return payload


def _get_transactions(
    household_external_id,
    since=None,
):
    household_id = urllib.parse.quote(
        household_external_id,
        safe="",
    )

    url = (
        f"{API_BASE_URL}"
        f"/households/{household_id}/transactions"
    )

    if since:
        query = urllib.parse.urlencode(
            {
                "since": since
            }
        )

        url = f"{url}?{query}"

    print(f"Trading URL: {url}")

    status, payload = _http_get_json(url)

    print(f"Trading response status: {status}")

    if status < 200 or status >= 300:
        raise RuntimeError(
            f"Trading service returned HTTP {status}"
        )

    return payload


def lambda_handler(event, context):

    # =========================================================
    # 1. Parse Salesforce CRM request
    # =========================================================

    try:
        crm = _parse_body(event)

    except Exception as exc:
        print(
            f"Invalid request payload: "
            f"{type(exc).__name__}: {str(exc)}"
        )

        return _response(
            400,
            {
                "detail": "Invalid request payload"
            },
        )

    household_external_id = crm.get(
        "household_external_id"
    )

    if not household_external_id:
        return _response(
            400,
            {
                "detail":
                    "household_external_id is required"
            },
        )

    print(
        f"household_external_id: "
        f"{household_external_id}"
    )

    # =========================================================
    # 2. Determine latest previous meeting
    # =========================================================

    events = crm.get("events") or []

    (
        last_meeting_event,
        last_meeting_datetime,
    ) = _find_last_meeting(events)

    last_meeting_date = None

    if last_meeting_datetime is not None:
        last_meeting_date = (
            last_meeting_datetime
            .date()
            .isoformat()
        )

    print(
        f"last_meeting_date: "
        f"{last_meeting_date}"
    )

    # =========================================================
    # 3. Retrieve Portfolio + Trading evidence
    # =========================================================

    try:
        portfolio = _get_portfolio(
            household_external_id
        )

        trading = _get_transactions(
            household_external_id,
            since=last_meeting_date,
        )

    except Exception as exc:
        print(
            f"Evidence retrieval failed: "
            f"{type(exc).__name__}: {str(exc)}"
        )

        return _response(
            502,
            {
                "detail":
                    "Unable to retrieve external evidence"
            },
        )

    # =========================================================
    # 4. Build combined evidence
    # =========================================================

    evidence = {
        "household_external_id":
            household_external_id,

        "reference_dates": {
            "generated_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "last_meeting_date":
                last_meeting_date,
        },

        "crm":
            crm,

        "portfolio":
            portfolio,

        "changes_since_last_meeting": {
            "last_meeting":
                last_meeting_event,

            "transactions":
                trading,
        },
    }

    # =========================================================
    # 5. Deterministic rules
    # =========================================================

    try:
        analysis = analyze_evidence(
            evidence
        )

    except Exception as exc:
        print(
            f"Deterministic analysis failed: "
            f"{type(exc).__name__}: {str(exc)}"
        )

        return _response(
            500,
            {
                "detail":
                    "Deterministic analysis failed"
            },
        )

    evidence[
        "deterministic_analysis"
    ] = analysis

    # =========================================================
    # 6. Controlled AI evidence
    # =========================================================

    try:
        ai_evidence = build_ai_evidence(
            evidence
        )

    except Exception as exc:
        print(
            f"AI evidence construction failed: "
            f"{type(exc).__name__}: {str(exc)}"
        )

        return _response(
            500,
            {
                "detail":
                    "AI evidence construction failed"
            },
        )

    # =========================================================
    # 7. Amazon Bedrock
    # =========================================================

    print(
        "Starting Bedrock advisor briefing generation"
    )

    try:
        advisor_briefing = generate_briefing(
            ai_evidence
        )

        print(
            "Bedrock generation completed"
        )

        # -----------------------------------------------------
        # TEMPORARY DIAGNOSTIC LOGGING
        #
        # We currently know Bedrock successfully generates JSON,
        # but citation validation is failing.
        #
        # Print ONLY the generated citation structure so we can
        # compare Nova's output with our deterministic validator.
        #
        # Do NOT print the complete CRM payload or AI evidence.
        # -----------------------------------------------------

        generated_citations = (
            advisor_briefing.get(
                "citations",
                []
            )
            if isinstance(
                advisor_briefing,
                dict
            )
            else []
        )

        print(
            "Generated citation structure: "
            + json.dumps(
                generated_citations,
                default=str
            )
        )

        # -----------------------------------------------------
        # Deterministic briefing validation
        # -----------------------------------------------------

        advisor_briefing = validate_briefing(
            advisor_briefing,
            ai_evidence,
        )

        print(
            "Advisor briefing validation completed"
        )

    except (
        BedrockResponseError,
        BriefingValidationError,
    ) as exc:

        print(
            f"Bedrock generation failed: "
            f"{type(exc).__name__}: "
            f"{str(exc)}"
        )

        return _response(
            500,
            {
                "detail":
                    "Advisor briefing generation failed"
            },
        )

    except Exception as exc:

        print(
            f"Unexpected Bedrock generation failure: "
            f"{type(exc).__name__}: "
            f"{str(exc)}"
        )

        return _response(
            500,
            {
                "detail":
                    "Advisor briefing generation failed"
            },
        )

    # =========================================================
    # 8. Successful response
    # =========================================================

    return _response(
        200,
        {
            **evidence,

            "deterministic_analysis":
                analysis,

            "ai_evidence":
                ai_evidence,

            "advisor_briefing":
                advisor_briefing,
        },
    )