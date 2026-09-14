import pandas as pd

tasks = pd.read_csv("data/tasks.csv")
contacts = pd.read_csv("data/contact_id_mapping.csv")
accounts = pd.read_csv("data/account_id_mapping.csv")

# Match each task to the correct Salesforce Contact
merged = tasks.merge(
    contacts[["Id", "Client_External_ID__c"]],
    left_on="Client_External_ID",
    right_on="Client_External_ID__c",
    how="left"
)

merged = merged.rename(columns={"Id": "WhoId"})

# Match each task to the correct Salesforce Account
merged = merged.merge(
    accounts[["Id", "Household_External_ID__c"]],
    left_on="Household_External_ID",
    right_on="Household_External_ID__c",
    how="left"
)

merged = merged.rename(columns={"Id": "WhatId"})

if merged["WhoId"].isnull().any():
    print("Some Tasks could not be matched to a Contact.")
    raise SystemExit(1)

if merged["WhatId"].isnull().any():
    print("Some Tasks could not be matched to an Account.")
    raise SystemExit(1)

output = merged[
    [
        "Activity_External_ID__c",
        "WhoId",
        "WhatId",
        "Subject",
        "Status",
        "Priority",
        "ActivityDate",
        "Description",
    ]
]

output.to_csv("data/task_upserts.csv", index=False)

print(f"Created task_upserts.csv with {len(output)} records.")