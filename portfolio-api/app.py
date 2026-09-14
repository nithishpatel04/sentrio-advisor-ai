from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI(title="Portfolio API")

portfolio_accounts = pd.read_csv("../data/portfolio_accounts.csv")
holdings = pd.read_csv("../data/holdings.csv")
performance = pd.read_csv("../data/performance.csv")


@app.get("/")
def root():
    return {
        "service": "Portfolio API",
        "status": "running"
    }


@app.get("/households/{household_id}/portfolio")
def get_household_portfolio(household_id: str):

    household_accounts = portfolio_accounts[
        portfolio_accounts["Household_External_ID"] == household_id
    ]

    if household_accounts.empty:
        raise HTTPException(
            status_code=404,
            detail="Household portfolio not found"
        )

    result = []

    for _, account in household_accounts.iterrows():

        account_id = account["Portfolio_Account_ID"]

        account_holdings = holdings[
            holdings["Portfolio_Account_ID"] == account_id
        ]

        account_performance = performance[
            performance["Portfolio_Account_ID"] == account_id
        ]

        result.append(
            {
                "portfolio_account_id": account_id,
                "account_type": account["Account_Type"],
                "market_value": float(account["Market_Value"]),
                "currency": account["Currency"],

                "holdings": account_holdings[
                    [
                        "Holding_ID",
                        "Symbol",
                        "Security_Name",
                        "Asset_Class",
                        "Market_Value",
                        "Portfolio_Weight",
                    ]
                ].to_dict(orient="records"),

                "performance": (
                    account_performance.to_dict(orient="records")[0]
                    if not account_performance.empty
                    else None
                ),
            }
        )

    return {
        "household_external_id": household_id,
        "portfolio_accounts": result
    }