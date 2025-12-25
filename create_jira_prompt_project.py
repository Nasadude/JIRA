#!/usr/bin/env python3
# ============================================================
#   JIRA CREATION SCRIPT — TEAM-MANAGED COMPATIBLE
#   Creates Task issues under Epics (multi-project aware)
# ============================================================

import os
import json
import argparse
import requests

# -------------------------------------------------------------
# Jira configuration
# -------------------------------------------------------------
JIRA_DOMAIN = "https://technating.atlassian.net"
JIRA_EMAIL = "mike@technating.io"
API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not API_TOKEN:
    print("ERROR: Set environment variable JIRA_API_TOKEN")
    exit(1)

AUTH = (JIRA_EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# === TEAM-MANAGED ISSUE TYPE (Task / Feature-compatible) ===
ISSUE_TYPE_ID = "10003"


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------
def infer_project_from_epic(epic_key: str) -> str:
    return epic_key.split("-")[0]


def prompt_project_key():
    try:
        value = input(
            "Enter Jira project key "
            "(press Enter to infer from epic): "
        ).strip()
        return value if value else None
    except KeyboardInterrupt:
        print("\nAborted.")
        exit(1)


# -------------------------------------------------------------
# Create a Jira Task under an Epic
# -------------------------------------------------------------
def create_issue(project_key, epic_key, summary, description, labels):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": project_key},
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

    response = requests.post(
        url, headers=HEADERS, auth=AUTH, json=payload
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"[CREATED] {issue_key} → {summary}")
        return issue_key

    print(
        f"[ERROR] Failed under {epic_key}: "
        f"{response.status_code} → {response.text}"
    )
    return None


# -------------------------------------------------------------
# Process JSON definitions
# -------------------------------------------------------------
def process_json(path):
    print(f"\n=== Creating Issues From {path} ===")

    default_project = prompt_project_key()

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

        project_key = (
            default_project
            if default_project
            else infer_project_from_epic(epic_key)
        )

        # Guardrail: prevent cross-project mismatch
        if not epic_key.startswith(project_key + "-"):
            print(
                f"[ERROR] Epic {epic_key} does not belong to "
                f"project {project_key}. Skipping."
            )
            continue

        print(f"\nCreating → {project_key} :: {epic_key} :: {summary}")

        issue_key = create_issue(
            project_key,
            epic_key,
            summary,
            description,
            labels
        )

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
    parser = argparse.ArgumentParser(
        description="Create Jira Task issues under Epics "
                    "(multi-project, team-managed compatible)."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="JSON file defining issues"
    )
    args = parser.parse_args()
    process_json(args.file)


if __name__ == "__main__":
    main()
