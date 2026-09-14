import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

contacts = pd.read_csv("data/contacts.csv")

subjects = [
    "Beneficiary update",
    "Address change",
    "Account access issue",
    "Document request",
    "Wire transfer inquiry",
    "Tax document request",
    "Profile information update",
    "Statement delivery issue",
]

priorities = ["Low", "Medium", "High"]
origins = ["Phone", "Email", "Web"]

cases = []

case_counter = 1

for _, contact in contacts.iterrows():

    # Not every client needs a Case.
    # Roughly 35% of clients will have one.
    if random.random() > 0.35:
        continue

    external_id = f"SR-{case_counter:05d}"

    subject = random.choice(subjects)
    priority = random.choices(
        priorities,
        weights=[0.25, 0.55, 0.20]
    )[0]

    origin = random.choice(origins)

    created_days_ago = random.randint(3, 300)
    created_date = datetime.today() - timedelta(days=created_days_ago)

    # About 65% of Cases are closed.
    is_closed = random.random() < 0.65

    if is_closed:
        status = "Closed"
        closed_after_days = random.randint(1, min(created_days_ago, 30))
        closed_date = created_date + timedelta(days=closed_after_days)

        # Make sure ClosedDate never goes into the future.
        if closed_date > datetime.today():
            closed_date = datetime.today()

    else:
        status = "New"
        closed_date = ""

    description = (
        f"Client requested assistance regarding {subject.lower()}."
    )

    cases.append(
        {
            "Service_Request_External_ID__c": external_id,
            "Client_External_ID": contact["Client_External_ID__c"],
            "Household_External_ID": contact["Household_External_ID"],
            "Subject": subject,
            "Description": description,
            "Status": status,
            "Priority": priority,
            "Origin": origin,
            "Created_Date_Helper": created_date.strftime("%Y-%m-%d"),
            "Closed_Date_Helper": (
                closed_date.strftime("%Y-%m-%d")
                if closed_date != ""
                else ""
            ),
        }
    )

    case_counter += 1

cases_df = pd.DataFrame(cases)

cases_df.to_csv("data/cases.csv", index=False)

print(f"Created cases.csv with {len(cases_df)} service requests.")