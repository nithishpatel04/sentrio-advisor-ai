import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

accounts = pd.read_csv("data/accounts.csv")

opportunity_types = [
    "New Investment",
    "Retirement Planning",
    "Estate Planning",
    "Insurance Review",
    "Cash Management",
    "Portfolio Consolidation",
]

stages = [
    "Prospecting",
    "Qualification",
    "Needs Analysis",
    "Proposal/Price Quote",
    "Negotiation/Review",
    "Closed Won",
    "Closed Lost",
]

opportunities = []

opportunity_counter = 1

for _, account in accounts.iterrows():

    # Roughly 40% of households will have an Opportunity
    if random.random() > 0.40:
        continue

    opportunity_type = random.choice(opportunity_types)
    stage = random.choice(stages)

    amount = random.choice([
        50000,
        75000,
        100000,
        150000,
        250000,
        500000,
    ])

    close_date = datetime.today() + timedelta(
        days=random.randint(15, 180)
    )

    # If already closed, make close date historical
    if stage in ["Closed Won", "Closed Lost"]:
        close_date = datetime.today() - timedelta(
            days=random.randint(5, 120)
        )

    external_id = f"OPP-{opportunity_counter:05d}"

    household_name = account["Name"]

    opportunities.append(
        {
            "Opportunity_External_ID__c": external_id,
            "Household_External_ID": account[
                "Household_External_ID__c"
            ],
            "Name": f"{household_name} - {opportunity_type}",
            "StageName": stage,
            "CloseDate": close_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "Type": opportunity_type,
            "Description": (
                f"Potential {opportunity_type.lower()} "
                f"opportunity for {household_name}."
            ),
        }
    )

    opportunity_counter += 1

opportunities_df = pd.DataFrame(opportunities)

opportunities_df.to_csv(
    "data/opportunities.csv",
    index=False
)

print(
    f"Created opportunities.csv with "
    f"{len(opportunities_df)} opportunities."
)