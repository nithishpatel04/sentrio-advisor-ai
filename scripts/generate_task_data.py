import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

contacts = pd.read_csv("data/contacts.csv")

task_subjects = [
    "Call client about missing documents",
    "Follow up on beneficiary update",
    "Review transfer request",
    "Schedule portfolio review",
    "Confirm address change",
    "Send requested documents",
    "Follow up on account access issue",
]

statuses = [
    "Not Started",
    "In Progress",
    "Completed",
]

priorities = [
    "Low",
    "Normal",
    "High",
]

tasks = []
task_counter = 1

for _, contact in contacts.iterrows():

    # Roughly 30% of clients will have a Task
    if random.random() > 0.30:
        continue

    subject = random.choice(task_subjects)
    status = random.choices(
        statuses,
        weights=[0.45, 0.30, 0.25]
    )[0]

    priority = random.choices(
        priorities,
        weights=[0.20, 0.60, 0.20]
    )[0]

    if status == "Completed":
        activity_date = (
            datetime.today()
            - timedelta(days=random.randint(1, 90))
        )
    else:
        activity_date = (
            datetime.today()
            + timedelta(days=random.randint(1, 45))
        )

    external_id = f"TASK-{task_counter:05d}"

    tasks.append(
        {
            "Activity_External_ID__c": external_id,
            "Client_External_ID": contact["Client_External_ID__c"],
            "Household_External_ID": contact["Household_External_ID"],
            "Subject": subject,
            "Status": status,
            "Priority": priority,
            "ActivityDate": activity_date.strftime("%Y-%m-%d"),
            "Description": (
                f"Advisor follow-up for {contact['FirstName']} "
                f"{contact['LastName']}."
            ),
        }
    )

    task_counter += 1

tasks_df = pd.DataFrame(tasks)

tasks_df.to_csv(
    "data/tasks.csv",
    index=False
)

print(
    f"Created tasks.csv with "
    f"{len(tasks_df)} tasks."
)