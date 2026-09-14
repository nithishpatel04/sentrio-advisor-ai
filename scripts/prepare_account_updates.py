import pandas as pd
import re

def normalize_phone(value):
    if pd.isna(value):
        return ""

    value = str(value)

    extension = ""
    match = re.search(r"x(\d+)", value)

    if match:
        extension = match.group(1)

    digits = re.sub(r"\D", "", value)

    # Remove leading North American country code 1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    return digits + extension


accounts = pd.read_csv("data/accounts.csv")
salesforce = pd.read_csv("data/salesforce_accounts.csv")

accounts["Phone_Normalized"] = accounts["Phone"].apply(normalize_phone)
salesforce["Phone_Normalized"] = salesforce["Phone"].apply(normalize_phone)

merged = accounts.merge(
    salesforce[["Id", "Name", "Phone_Normalized"]],
    on=["Name", "Phone_Normalized"],
    how="left"
)

if merged["Id"].isnull().any():
    print("Some households were not matched:")
    print(
        merged[merged["Id"].isnull()][
            ["Household_External_ID__c", "Name", "Phone"]
        ]
    )
    raise SystemExit(1)

if merged["Id"].duplicated().any():
    print("ERROR: Multiple CSV rows matched the same Salesforce Account.")
    raise SystemExit(1)

columns = [
    "Id",
    "Household_External_ID__c",
    "Name",
    "Phone",
    "Client_Since__c",
    "Client_Tier__c",
    "Risk_Profile__c",
    "Risk_Profile_Last_Reviewed__c",
    "Preferred_Contact_Method__c",
    "Description",
]

merged[columns].to_csv(
    "data/account_updates.csv",
    index=False
)

print(f"Created account_updates.csv with {len(merged)} records.")