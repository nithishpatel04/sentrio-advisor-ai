import csv
import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "lambda_data", "transactions.csv")


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _read_transactions():
    with open(DATA_PATH, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def lambda_handler(event, context):
    print("Received event:", event)

    path_parameters = event.get("pathParameters") or {}
    household_id = path_parameters.get("household_id")
    query_parameters = event.get("queryStringParameters") or {}
    since = query_parameters.get("since")
    print("Household ID:", household_id)
    print("Since:", since)

    if not household_id:
        return _response(400, {"detail": "household_id is required"})

    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, "%Y-%m-%d").date()
        except ValueError:
            return _response(400, {"detail": "Invalid since date. Use YYYY-MM-DD."})

    matching_transactions = [
        transaction
        for transaction in _read_transactions()
        if transaction["Household_External_ID"] == household_id
    ]

    if since_date is not None:
        matching_transactions = [
            transaction
            for transaction in matching_transactions
            if datetime.strptime(transaction["Transaction_Date"], "%Y-%m-%d").date()
            >= since_date
        ]

    matching_transactions.sort(key=lambda transaction: transaction["Transaction_Date"], reverse=True)
    print("Number of transactions returned:", len(matching_transactions))

    if not matching_transactions:
        return _response(404, {"detail": "No transactions found for household"})

    return _response(
        200,
        {
            "household_external_id": household_id,
            "transaction_count": len(matching_transactions),
            "transactions": matching_transactions,
        },
    )