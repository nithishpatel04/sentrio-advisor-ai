import pandas as pd

events = pd.read_csv("data/events.csv")
contacts = pd.read_csv("data/contact_id_mapping.csv")
accounts = pd.read_csv("data/account_id_mapping.csv")

# Resolve Contact
merged = events.merge(
    contacts[["Id", "Client_External_ID__c"]],
    left_on="Client_External_ID",
    right_on="Client_External_ID__c",
    how="left"
)

merged = merged.rename(columns={"Id": "WhoId"})

# Resolve Account / Household
merged = merged.merge(
    accounts[["Id", "Household_External_ID__c"]],
    left_on="Household_External_ID",
    right_on="Household_External_ID__c",
    how="left"
)

merged = merged.rename(columns={"Id": "WhatId"})

if merged["WhoId"].isnull().any():
    print("Some Events could not be matched to a Contact.")
    raise SystemExit(1)

if merged["WhatId"].isnull().any():
    print("Some Events could not be matched to an Account.")
    raise SystemExit(1)

output = merged[
    [
        "Activity_External_ID__c",
        "WhoId",
        "WhatId",
        "Subject",
        "StartDateTime",
        "EndDateTime",
        "Location",
        "Description",
    ]
]

output.to_csv("data/event_upserts.csv", index=False)

print(f"Created event_upserts.csv with {len(output)} records.")