import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

portfolio_accounts = pd.read_csv(
    "data/portfolio_accounts.csv"
)

symbols = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "VTI",
    "BND",
    "SPY",
]

transaction_types = [
    "BUY",
    "SELL",
]

transactions = []

transaction_counter = 1

for _, account in portfolio_accounts.iterrows():

    portfolio_account_id = account[
        "Portfolio_Account_ID"
    ]

    household_id = account[
        "Household_External_ID"
    ]

    # Each portfolio account gets 2–8 transactions
    transaction_count = random.randint(2, 8)

    for _ in range(transaction_count):

        transaction_date = (
            datetime.today()
            - timedelta(days=random.randint(1, 365))
        )

        transaction_type = random.choice(
            transaction_types
        )

        symbol = random.choice(symbols)

        quantity = random.randint(5, 200)

        price = round(
            random.uniform(25, 500),
            2
        )

        total_amount = round(
            quantity * price,
            2
        )

        transactions.append(
            {
                "Transaction_ID": (
                    f"TXN-{transaction_counter:06d}"
                ),
                "Household_External_ID": household_id,
                "Portfolio_Account_ID": portfolio_account_id,
                "Transaction_Date": transaction_date.strftime(
                    "%Y-%m-%d"
                ),
                "Transaction_Type": transaction_type,
                "Symbol": symbol,
                "Quantity": quantity,
                "Price": price,
                "Total_Amount": total_amount,
                "Currency": "CAD",
            }
        )

        transaction_counter += 1

transactions_df = pd.DataFrame(transactions)

transactions_df.to_csv(
    "data/transactions.csv",
    index=False
)

print(
    f"Created {len(transactions_df)} transactions."
)