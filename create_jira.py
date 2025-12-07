#!/usr/bin/env python3
# ============================================================
#   JIRA CREATION SCRIPT — CERTIFICATES FOR OISS PHASE 1
#   Creates Feature issues under existing Epics (CPG-7..14)
#   Compatible with team-managed Jira project CPG
# ============================================================

import os
import json
import argparse
import requests

# Jira configuration
JIRA_DOMAIN = "https://technating.atlassian.net"
JIRA_EMAIL = "mike@technating.io"
API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not API_TOKEN:
    print("ERROR: Set environment variable JIRA_API_TOKEN")
    exit(1)

AUTH = (JIRA_EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# Allowed issue type for certificates
ISSUE_TYPE_ID = "10003"  # Feature


# -------------------------------------------------------------
# Create a Jira issue
# -------------------------------------------------------------
def create_issue(epic_key, summary, description, labels):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": "CPG"},
            "summary": summary,

            # Atlassian Document Format
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },

            "issuetype": {"id": ISSUE_TYPE_ID},
            "parent": {"key": epic_key},
            "labels": labels
        }
    }

    response = requests.post(url, headers=HEADERS, auth=AUTH, json=payload)

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"[CREATED] {issue_key} → {summary}")
        return issue_key

    print(f"[ERROR] Issue creation failed for {epic_key}: {response.status_code} → {response.text}")
    return None

# -------------------------------------------------------------
# Process JSON certificate definitions
# -------------------------------------------------------------
def process_json(path):
    print(f"\n=== Creating Certificate Issues From {path} ===")

    with open(path, "r") as f:
        items = json.load(f)

    update_entries = []

    for entry in items:
        try:
            rtm = entry["rtm"]
            epic_key = entry["epic"]
            summary = entry["summary"]
            description = entry["description"]
            labels = entry.get("labels", [])

        except KeyError as e:
            print(f"[SKIP] Missing field in entry: {e}")
            continue

        print(f"\nCreating for Epic {epic_key} → {summary}")

        issue_key = create_issue(epic_key, summary, description, labels)

        if issue_key:
            update_entries.append({
                "issue": issue_key,
                "status": "To Do",
                "comment": f"RTM {rtm} certificate created.",
                "labels": labels,
                "points": 0
            })

    # Write JSON for update_jira.py
    update_file = os.path.splitext(path)[0] + "_update.json"
    with open(update_file, "w") as f:
        json.dump(update_entries, f, indent=2)

    print("\n=== DONE ===")
    print(f"Created {len(update_entries)} Jira certificate issues")
    print(f"Update file saved: {update_file}")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Create Jira certificate issues.")
    parser.add_argument("--file", required=True, help="JSON file defining certificate issues")

    args = parser.parse_args()
    process_json(args.file)


if __name__ == "__main__":
    main()
