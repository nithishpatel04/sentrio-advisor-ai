import csv
import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "lambda_data")


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def lambda_handler(event, context):
    print("Received event:", event)

    path_parameters = event.get("pathParameters") or {}
    household_id = path_parameters.get("household_id")
    print("Household ID:", household_id)

    if not household_id:
        return _response(400, {"detail": "household_id is required"})

    accounts = _read_csv("portfolio_accounts.csv")
    holdings = _read_csv("holdings.csv")
    performance = _read_csv("performance.csv")

    matching_accounts = [
        account
        for account in accounts
        if account["Household_External_ID"] == household_id
    ]
    print("Number of accounts found:", len(matching_accounts))

    if not matching_accounts:
        return _response(404, {"detail": "Household portfolio not found"})

    portfolio_accounts = []
    for account in matching_accounts:
        account_id = account["Portfolio_Account_ID"]
        account_holdings = [
            holding
            for holding in holdings
            if holding["Portfolio_Account_ID"] == account_id
        ]
        account_performance = next(
            (
                record
                for record in performance
                if record["Portfolio_Account_ID"] == account_id
            ),
            {},
        )

        portfolio_accounts.append(
            {
                "portfolio_account_id": account_id,
                "account_type": account["Account_Type"],
                "market_value": account["Market_Value"],
                "currency": account["Currency"],
                "holdings": account_holdings,
                "performance": account_performance,
            }
        )

    return _response(
        200,
        {
            "household_external_id": household_id,
            "accounts": portfolio_accounts,
        },
    )