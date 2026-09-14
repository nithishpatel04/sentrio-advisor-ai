import pandas as pd

cases = pd.read_csv("data/cases.csv")
contacts = pd.read_csv("data/contact_id_mapping.csv")

merged = cases.merge(
    contacts,
    left_on="Client_External_ID",
    right_on="Client_External_ID__c",
    how="left"
)

if merged["Id"].isnull().any():
    print("Some Cases could not be matched to a Salesforce Contact:")
    print(
        merged[merged["Id"].isnull()][
            [
                "Service_Request_External_ID__c",
                "Client_External_ID",
                "Household_External_ID",
            ]
        ]
    )
    raise SystemExit(1)

output = pd.DataFrame(
    {
        "Service_Request_External_ID__c": merged[
            "Service_Request_External_ID__c"
        ],
        "ContactId": merged["Id"],
        "AccountId": merged["AccountId"],
        "Subject": merged["Subject"],
        "Description": merged["Description"],
        "Status": merged["Status"],
        "Priority": merged["Priority"],
        "Origin": merged["Origin"],
    }
)

output.to_csv("data/case_upserts.csv", index=False)

print(f"Created case_upserts.csv with {len(output)} records.")