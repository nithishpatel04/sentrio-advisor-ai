from fastapi import FastAPI, HTTPException, Query
import pandas as pd

app = FastAPI(title="Trading API")

transactions = pd.read_csv("../data/transactions.csv")


@app.get("/")
def root():
    return {
        "service": "Trading API",
        "status": "running"
    }


@app.get("/households/{household_id}/transactions")
def get_household_transactions(
    household_id: str,
    since: str | None = Query(default=None)
):
    household_transactions = transactions[
        transactions["Household_External_ID"] == household_id
    ].copy()

    if household_transactions.empty:
        raise HTTPException(
            status_code=404,
            detail="No transactions found for household"
        )

    # Convert dates so we can filter them correctly
    household_transactions["Transaction_Date"] = pd.to_datetime(
        household_transactions["Transaction_Date"]
    )

    # Optional filtering:
    # /transactions?since=2026-06-01
    if since:
        try:
            since_date = pd.to_datetime(since)

            household_transactions = household_transactions[
                household_transactions["Transaction_Date"] >= since_date
            ]

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid since date. Use YYYY-MM-DD."
            )

    household_transactions = household_transactions.sort_values(
        by="Transaction_Date",
        ascending=False
    )

    # Convert Timestamp back to string for clean JSON
    household_transactions["Transaction_Date"] = (
        household_transactions["Transaction_Date"]
        .dt.strftime("%Y-%m-%d")
    )

    return {
        "household_external_id": household_id,
        "transaction_count": len(household_transactions),
        "transactions": household_transactions.to_dict(
            orient="records"
        ),
    }