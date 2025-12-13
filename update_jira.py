#!/usr/bin/env python3
# ===================================================================
#   UPDATE JIRA ISSUES + ATTACH CERTIFICATES + TEST ARTIFACTS
#   Supports: status, comments, labels, story points, assignee,
#             certificate PDFs, and explicit test file attachments
# ===================================================================

import os
import json
import argparse
import requests

# -----------------------------
# Jira Configuration
# -----------------------------
JIRA_DOMAIN = "https://technating.atlassian.net"
JIRA_EMAIL = "mike@technating.io"
API_TOKEN = os.getenv("JIRA_API_TOKEN")

AUTH = (JIRA_EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
# -----------------------------
# Project Root Resolution
# -----------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Directory where category/severity PDFs live
CERT_DIR = "/Users/michaelritchson/desktop/development/JIRA/certificates"


# ============================================================
# Certificate Attachment Logic
# ============================================================
def attach_certificate(issue_key, category, severity):
    """
    Attempts multiple filename patterns:
    maneuver_LOW.pdf, maneuver_low.pdf, maneuver-low.pdf, etc.
    """
    base = f"{category}_{severity}"
    possible_filenames = [
        f"{base}.pdf",
        f"{base.lower()}.pdf",
        f"{category.lower()}_{severity.lower()}.pdf",
        f"{category.upper()}_{severity.upper()}.pdf",
        f"{category}-{severity}.pdf",
        f"{category.lower()}-{severity.lower()}.pdf"
    ]

    for fname in possible_filenames:
        path = os.path.join(CERT_DIR, fname)
        if os.path.exists(path):
            return upload_file(issue_key, path)

    print(f"[WARN] No PDF found for category={category}, severity={severity}")
    return False


# ============================================================
# Generic File Attachment (logs, CSVs, JSON, etc.)
# ============================================================
def upload_file(issue_key, file_path):
    """
    Uploads any file type to a Jira issue.
    """
    print(f"[DEBUG] Resolved attachment path: {file_path}")
    if not os.path.exists(file_path):
        print(f"[WARN] Attachment not found: {file_path}")
        return False

    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/attachments"

    # DO NOT send Content-Type here
    headers = {
        "X-Atlassian-Token": "no-check",
        "Accept": "application/json"
    }

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(
            url,
            headers=headers,
            auth=AUTH,
            files=files
        )

    if response.status_code in (200, 201):
        print(f"[ATTACHED] {os.path.basename(file_path)} → {issue_key}")
        return True

    print(
        f"[ERROR] Failed to attach {file_path} to {issue_key}\n"
        f"        Status: {response.status_code}\n"
        f"        Response: {response.text}"
    )
    return False



# ============================================================
# Jira Update Functions
# ============================================================
def update_status(issue_key, status):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions"
    transitions = requests.get(url, headers=HEADERS, auth=AUTH).json().get("transitions", [])

    transition_id = None
    for t in transitions:
        if t["name"].lower() == status.lower():
            transition_id = t["id"]
            break

    if not transition_id:
        print(f"[WARN] Cannot transition {issue_key} → {status}")
        return

    payload = {"transition": {"id": transition_id}}
    r = requests.post(url, headers=HEADERS, auth=AUTH, json=payload)
    print(f"[STATUS] {issue_key}: {status} ({r.status_code})")


def add_comment(issue_key, comment):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/comment"

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph",
                 "content": [{"type": "text", "text": comment}]}
            ]
        }
    }

    r = requests.post(url, headers=HEADERS, auth=AUTH, json=payload)
    print(f"[COMMENT] {issue_key}: {r.status_code}")


def add_labels(issue_key, labels):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}"
    payload = {"update": {"labels": [{"add": label} for label in labels]}}
    r = requests.put(url, headers=HEADERS, auth=AUTH, json=payload)
    print(f"[LABELS] {issue_key}: {r.status_code}")


def assign_to_me(issue_key):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/assignee"
    me = requests.get(f"{JIRA_DOMAIN}/rest/api/3/myself",
                      headers=HEADERS, auth=AUTH).json()
    acct = me["accountId"]

    r = requests.put(url, headers=HEADERS, auth=AUTH,
                     json={"accountId": acct})
    print(f"[ASSIGNEE] {issue_key}: {r.status_code}")


def update_story_points(issue_key, points):
    url = f"{JIRA_DOMAIN}/rest/api/3/field"
    fields = requests.get(url, headers=HEADERS, auth=AUTH).json()

    sp_field = None
    for f in fields:
        if "story point" in f.get("name", "").lower():
            sp_field = f["id"]
            break

    if not sp_field:
        print(f"[POINTS] No Story Points field found. Skipping for {issue_key}")
        return

    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}"
    payload = {"fields": {sp_field: points}}
    r = requests.put(url, headers=HEADERS, auth=AUTH, json=payload)
    print(f"[POINTS] {issue_key}: {r.status_code}")

# ============================================================
# Work Log (Time Tracking)
# ============================================================
def add_worklog(issue_key, time_spent, comment=None):
    """
    Adds a work log entry to a Jira issue.
    time_spent examples: '1h', '30m', '2h 15m'
    """
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/worklog"

    payload = {
        "timeSpent": time_spent
    }

    if comment:
        payload["comment"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }
            ]
        }

    r = requests.post(url, headers=HEADERS, auth=AUTH, json=payload)

    if r.status_code in (200, 201):
        print(f"[WORKLOG] {issue_key}: {time_spent}")
    else:
        print(f"[ERROR] Failed to log work for {issue_key}: "
              f"{r.status_code} → {r.text}")



# ============================================================
# Batch Processor
# ============================================================
def process_rtm(path):
    with open(path, "r") as f:
        items = json.load(f)

    for entry in items:
        issue = entry["issue"]
        print(f"\n=== Updating {issue} ===")

        # Core updates
        if "status" in entry:
            update_status(issue, entry["status"])

        if "comment" in entry:
            add_comment(issue, entry["comment"])

        assign_to_me(issue)

        if "labels" in entry:
            add_labels(issue, entry["labels"])

        if "points" in entry:
            update_story_points(issue, entry["points"])

        # ----------------------------------------------------
        # Work Log (explicit, auditable)
        # ----------------------------------------------------
        worklog = entry.get("worklog")
        if worklog:
            add_worklog(
                issue,
                worklog.get("timeSpent"),
                worklog.get("comment")
            )


        # ----------------------------------------------------
        # Certificate PDFs (category + severity)
        # ----------------------------------------------------
        category = entry.get("category")
        severity = entry.get("severity")

        if category and severity:
            attach_certificate(issue, category, severity)

        # ----------------------------------------------------
        # Explicit attachments (test logs, CSVs, JSON, etc.)
        # ----------------------------------------------------
        attachments = entry.get("attachments", [])
        for rel_path in attachments:
            abs_path = (
                rel_path
                if os.path.isabs(rel_path)
                else os.path.join(PROJECT_ROOT, rel_path)
            )
            upload_file(issue, abs_path)



# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Update Jira issues and attach certificates and test artifacts."
    )
    parser.add_argument("--rtm", required=True, help="JSON update file")

    args = parser.parse_args()
    process_rtm(args.rtm)


if __name__ == "__main__":
    main()
