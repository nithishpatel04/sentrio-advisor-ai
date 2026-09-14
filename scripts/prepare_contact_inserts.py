import pandas as pd

contacts = pd.read_csv("data/contacts.csv")
accounts = pd.read_csv("data/account_id_mapping.csv")

merged = contacts.merge(
    accounts,
    left_on="Household_External_ID",
    right_on="Household_External_ID__c",
    how="left"
)

if merged["Id"].isnull().any():
    print("Some contacts could not be matched to an Account:")
    print(
        merged[merged["Id"].isnull()][
            ["Client_External_ID__c", "Household_External_ID", "FirstName", "LastName"]
        ]
    )
    raise SystemExit(1)

output = merged[
    [
        "Client_External_ID__c",
        "FirstName",
        "LastName",
        "Email",
        "Phone",
        "Title",
        "Id",
    ]
].copy()

output = output.rename(columns={"Id": "AccountId"})

output.to_csv("data/contact_inserts.csv", index=False)

print(f"Created contact_inserts.csv with {len(output)} records.")