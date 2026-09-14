from faker import Faker
from pathlib import Path
from datetime import date, timedelta
import csv
import random

fake = Faker("en_CA")
random.seed(42)
Faker.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HOUSEHOLD_COUNT = 50

CLIENT_TIERS = ["Platinum", "Gold", "Silver", "Standard"]
RISK_PROFILES = [
    "Conservative",
    "Moderately Conservative",
    "Balanced",
    "Growth",
    "Aggressive",
]
CONTACT_METHODS = ["Email", "Phone", "SMS", "In Person"]


def random_past_date(min_days_ago, max_days_ago):
    days_ago = random.randint(min_days_ago, max_days_ago)
    return date.today() - timedelta(days=days_ago)


accounts = []
contacts = []

client_counter = 1

for household_number in range(1, HOUSEHOLD_COUNT + 1):

    household_id = f"HH-{household_number:04d}"

    last_name = fake.last_name()

    client_since = random_past_date(
        min_days_ago=365,
        max_days_ago=365 * 15
    )

    # Most households have a recent risk review,
    # but some deliberately contain stale information.
    if household_number % 10 == 0:
        risk_review_date = random_past_date(
            min_days_ago=550,
            max_days_ago=900
        )
    else:
        risk_review_date = random_past_date(
            min_days_ago=20,
            max_days_ago=330
        )

    account = {
        "Household_External_ID__c": household_id,
        "Name": f"{last_name} Household",
        "Phone": fake.phone_number(),
        "Client_Since__c": client_since.isoformat(),
        "Client_Tier__c": random.choice(CLIENT_TIERS),
        "Risk_Profile__c": random.choice(RISK_PROFILES),
        "Risk_Profile_Last_Reviewed__c": risk_review_date.isoformat(),
        "Preferred_Contact_Method__c": random.choice(CONTACT_METHODS),
        "Description": "Synthetic household generated for SentrioStack Advisor Briefing demonstration.",
    }

    accounts.append(account)

    # Generate between 2 and 4 people in each household.
    number_of_clients = random.randint(2, 4)

    for person_number in range(number_of_clients):

        client_id = f"CL-{client_counter:05d}"
        client_counter += 1

        first_name = fake.first_name()

        # First two people share the household surname.
        # Additional members may have a different surname.
        if person_number < 2:
            contact_last_name = last_name
        else:
            contact_last_name = (
                last_name if random.random() < 0.7
                else fake.last_name()
            )

        contact = {
            "Client_External_ID__c": client_id,
            "Household_External_ID": household_id,
            "FirstName": first_name,
            "LastName": contact_last_name,
            "Email": fake.unique.email(),
            "Phone": fake.phone_number(),
            "Title": random.choice(
                [
                    "Executive",
                    "Business Owner",
                    "Physician",
                    "Engineer",
                    "Consultant",
                    "Retired",
                    "Director",
                    "Attorney",
                ]
            ),
        }

        contacts.append(contact)


account_file = DATA_DIR / "accounts.csv"

with account_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=accounts[0].keys()
    )
    writer.writeheader()
    writer.writerows(accounts)


contact_file = DATA_DIR / "contacts.csv"

with contact_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=contacts[0].keys()
    )
    writer.writeheader()
    writer.writerows(contacts)


print(f"Generated {len(accounts)} households")
print(f"Generated {len(contacts)} clients")
print(f"Accounts file: {account_file}")
print(f"Contacts file: {contact_file}")