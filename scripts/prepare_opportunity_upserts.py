import pandas as pd

opportunities = pd.read_csv("data/opportunities.csv")
accounts = pd.read_csv("data/account_id_mapping.csv")

merged = opportunities.merge(
    accounts,
    left_on="Household_External_ID",
    right_on="Household_External_ID__c",
    how="left"
)

if merged["Id"].isnull().any():
    print("Some Opportunities could not be matched to a Salesforce Account:")
    print(
        merged[merged["Id"].isnull()][
            [
                "Opportunity_External_ID__c",
                "Household_External_ID",
                "Name",
            ]
        ]
    )
    raise SystemExit(1)

output = pd.DataFrame(
    {
        "Opportunity_External_ID__c": merged["Opportunity_External_ID__c"],
        "AccountId": merged["Id"],
        "Name": merged["Name"],
        "StageName": merged["StageName"],
        "CloseDate": merged["CloseDate"],
        "Amount": merged["Amount"],
        "Type": merged["Type"],
        "Description": merged["Description"],
    }
)

output.to_csv("data/opportunity_upserts.csv", index=False)

print(
    f"Created opportunity_upserts.csv with "
    f"{len(output)} records."
)