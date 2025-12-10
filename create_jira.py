#!/usr/bin/env python3
# ============================================================
#   JIRA CREATION SCRIPT — TEAM-MANAGED COMPATIBLE
#   Creates Task issues under Epics (CPG-7..15)
#   Project: CPG (projectId = 10033)
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

# === TEAM-MANAGED ISSUE TYPE (Task) ===
ISSUE_TYPE_ID = "10003"    # FEATURE– team-managed parent-compatible



# -------------------------------------------------------------
# Create a Jira Task under an Epic
# -------------------------------------------------------------
def create_issue(epic_key, summary, description, labels):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": "CPG"},
            "summary": summary,

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

            # Team-managed: parent MUST be epic_key
            "parent": {"key": epic_key},

            "labels": labels
        }
    }

    response = requests.post(url, headers=HEADERS, auth=AUTH, json=payload)

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"[CREATED] {issue_key} → {summary}")
        return issue_key

    print(f"[ERROR] Epic {epic_key} failed: {response.status_code} → {response.text}")
    return None


# -------------------------------------------------------------
# Process JSON definitions (certificate or Phase 1 items)
# -------------------------------------------------------------
def process_json(path):
    print(f"\n=== Creating Issues From {path} ===")

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
            print(f"[SKIP] Missing field: {e}")
            continue

        print(f"\nCreating → {epic_key} :: {summary}")

        issue_key = create_issue(epic_key, summary, description, labels)

        if issue_key:
            update_entries.append({
                "issue": issue_key,
                "status": "To Do",
                "comment": f"{rtm} created (auto-generated).",
                "labels": labels,
                "points": 0
            })

    update_file = os.path.splitext(path)[0] + "_update.json"
    with open(update_file, "w") as f:
        json.dump(update_entries, f, indent=2)

    print("\n=== DONE ===")
    print(f"Issues created: {len(update_entries)}")
    print(f"Update file saved: {update_file}")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Create Jira Task issues under Epics.")
    parser.add_argument("--file", required=True, help="JSON file defining issues")
    args = parser.parse_args()
    process_json(args.file)


if __name__ == "__main__":
    main()
