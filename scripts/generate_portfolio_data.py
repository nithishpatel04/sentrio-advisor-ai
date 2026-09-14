import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

accounts = pd.read_csv("data/accounts.csv")

portfolio_accounts = []
holdings = []
performance = []

portfolio_account_counter = 1
holding_counter = 1

securities = [
    ("AAPL", "Apple Inc.", "Equity"),
    ("MSFT", "Microsoft Corp.", "Equity"),
    ("GOOGL", "Alphabet Inc.", "Equity"),
    ("AMZN", "Amazon.com Inc.", "Equity"),
    ("VTI", "Vanguard Total Stock Market ETF", "ETF"),
    ("BND", "Vanguard Total Bond Market ETF", "ETF"),
    ("SPY", "SPDR S&P 500 ETF", "ETF"),
]

account_types = [
    "Individual Investment Account",
    "Retirement Account",
    "TFSA",
    "RRSP",
]

for _, household in accounts.iterrows():

    household_id = household["Household_External_ID__c"]

    # Each household gets 1–3 portfolio accounts
    num_accounts = random.randint(1, 3)

    for _ in range(num_accounts):

        portfolio_account_id = f"PA-{portfolio_account_counter:05d}"

        account_type = random.choice(account_types)

        account_value = random.randint(50000, 750000)

        portfolio_accounts.append(
            {
                "Portfolio_Account_ID": portfolio_account_id,
                "Household_External_ID": household_id,
                "Account_Type": account_type,
                "Market_Value": account_value,
                "Currency": "CAD",
            }
        )

        # Each portfolio account gets 3–6 holdings
        selected_securities = random.sample(
            securities,
            k=random.randint(3, 6)
        )

        weights = [
            random.uniform(0.05, 0.40)
            for _ in selected_securities
        ]

        total_weight = sum(weights)

        normalized_weights = [
            weight / total_weight
            for weight in weights
        ]

        for security, weight in zip(
            selected_securities,
            normalized_weights
        ):

            symbol, security_name, asset_class = security

            holding_value = round(
                account_value * weight,
                2
            )

            holdings.append(
                {
                    "Holding_ID": f"HLD-{holding_counter:06d}",
                    "Portfolio_Account_ID": portfolio_account_id,
                    "Symbol": symbol,
                    "Security_Name": security_name,
                    "Asset_Class": asset_class,
                    "Market_Value": holding_value,
                    "Portfolio_Weight": round(
                        weight * 100,
                        2
                    ),
                }
            )

            holding_counter += 1

        # Performance metrics
        portfolio_return_1y = round(
            random.uniform(-8, 18),
            2
        )

        benchmark_return_1y = round(
            random.uniform(-5, 15),
            2
        )

        performance.append(
            {
                "Portfolio_Account_ID": portfolio_account_id,
                "As_Of_Date": datetime.today().strftime("%Y-%m-%d"),
                "Portfolio_Return_1Y": portfolio_return_1y,
                "Benchmark_Return_1Y": benchmark_return_1y,
                "Relative_Performance": round(
                    portfolio_return_1y - benchmark_return_1y,
                    2
                ),
            }
        )

        portfolio_account_counter += 1


pd.DataFrame(
    portfolio_accounts
).to_csv(
    "data/portfolio_accounts.csv",
    index=False
)

pd.DataFrame(
    holdings
).to_csv(
    "data/holdings.csv",
    index=False
)

pd.DataFrame(
    performance
).to_csv(
    "data/performance.csv",
    index=False
)

print(
    f"Created {len(portfolio_accounts)} portfolio accounts."
)

print(
    f"Created {len(holdings)} holdings."
)

print(
    f"Created {len(performance)} performance records."
)