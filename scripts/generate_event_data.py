import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

accounts = pd.read_csv("data/accounts.csv")
contacts = pd.read_csv("data/contacts.csv")

event_subjects = [
    "Annual Review Meeting",
    "Portfolio Review",
    "Retirement Planning Meeting",
    "Estate Planning Discussion",
    "Investment Strategy Review",
]

events = []
event_counter = 1

for _, account in accounts.iterrows():

    # Roughly 60% of households will have meeting history
    if random.random() > 0.60:
        continue

    household_id = account["Household_External_ID__c"]

    household_contacts = contacts[
        contacts["Household_External_ID"] == household_id
    ]

    if household_contacts.empty:
        continue

    contact = household_contacts.iloc[0]

    # Create a past meeting
    past_start = datetime.today() - timedelta(
        days=random.randint(30, 365)
    )

    past_end = past_start + timedelta(hours=1)

    events.append(
        {
            "Activity_External_ID__c": f"EVENT-{event_counter:05d}",
            "Client_External_ID": contact["Client_External_ID__c"],
            "Household_External_ID": household_id,
            "Subject": random.choice(event_subjects),
            "StartDateTime": past_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "EndDateTime": past_end.strftime("%Y-%m-%dT%H:%M:%S"),
            "Location": "Advisor Office",
            "Description": "Completed client advisory meeting.",
        }
    )

    event_counter += 1

    # About half of those households also get an upcoming meeting
    if random.random() < 0.50:

        future_start = datetime.today() + timedelta(
            days=random.randint(7, 90)
        )

        future_end = future_start + timedelta(hours=1)

        events.append(
            {
                "Activity_External_ID__c": f"EVENT-{event_counter:05d}",
                "Client_External_ID": contact["Client_External_ID__c"],
                "Household_External_ID": household_id,
                "Subject": random.choice(event_subjects),
                "StartDateTime": future_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "EndDateTime": future_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "Location": "Virtual",
                "Description": "Upcoming client advisory meeting.",
            }
        )

        event_counter += 1

events_df = pd.DataFrame(events)

events_df.to_csv(
    "data/events.csv",
    index=False
)

print(
    f"Created events.csv with "
    f"{len(events_df)} events."
)