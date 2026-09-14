from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
from datetime import datetime

app = FastAPI(title="Advisor Briefing Service")

SENTRIO_API_BASE_URL = os.getenv(
    "SENTRIO_API_BASE_URL",
    "https://5ty7d7s890.execute-api.us-east-1.amazonaws.com",
).rstrip("/")


class CRMEvent(BaseModel):
    subject: str
    start_datetime: str


class CRMEvidence(BaseModel):
    household_external_id: str
    household_name: Optional[str] = None
    contacts: List[dict] = []
    cases: List[dict] = []
    opportunities: List[dict] = []
    tasks: List[dict] = []
    events: List[CRMEvent] = []


@app.get("/")
def root():
    return {
        "service": "Advisor Briefing Service",
        "status": "running"
    }


@app.post("/briefings/evidence")
def build_evidence(crm: CRMEvidence):

    household_id = crm.household_external_id
    print("Household ID:", household_id)

    # ----------------------------
    # 1. Determine last meeting
    # ----------------------------

    last_meeting_date = None
    now = datetime.now()

    past_events = []

    for event in crm.events:
        try:
            event_datetime = datetime.fromisoformat(
                event.start_datetime.replace("Z", "+00:00")
            )

            # Simple POC comparison
            event_datetime = event_datetime.replace(tzinfo=None)

            if event_datetime < now:
                past_events.append((event_datetime, event))

        except ValueError:
            continue

    if past_events:
        past_events.sort(
            key=lambda item: item[0],
            reverse=True
        )

        last_meeting_date = past_events[0][0].strftime("%Y-%m-%d")

    print("Last meeting date:", last_meeting_date)

    # ----------------------------
    # 2. Retrieve Portfolio data
    # ----------------------------

    portfolio_url = (
        f"{SENTRIO_API_BASE_URL}/households/{household_id}/portfolio"
    )
    print("Portfolio URL:", portfolio_url)

    try:
        portfolio_response = requests.get(
            portfolio_url,
            timeout=10
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Portfolio API unavailable"
        )

    print("Portfolio response status:", portfolio_response.status_code)

    if portfolio_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve portfolio data"
        )

    portfolio_data = portfolio_response.json()

    # ----------------------------
    # 3. Retrieve Trading data
    # ----------------------------

    trading_url = (
        f"{SENTRIO_API_BASE_URL}/households/{household_id}/transactions"
    )
    print("Trading URL:", trading_url)

    params = {}

    if last_meeting_date:
        params["since"] = last_meeting_date

    try:
        trading_response = requests.get(
            trading_url,
            params=params,
            timeout=10
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Trading API unavailable"
        )

    print("Trading response status:", trading_response.status_code)

    if trading_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve trading data"
        )

    trading_data = trading_response.json()

    # ----------------------------
    # 4. Build evidence package
    # ----------------------------

    return {
        "household_external_id": household_id,

        "reference_dates": {
            "last_meeting_date": last_meeting_date
        },

        "crm": crm.model_dump(),

        "portfolio": portfolio_data,

        "changes_since_last_meeting": {
            "transactions": trading_data
        }
    }