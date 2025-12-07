#!/usr/bin/env python3
# ===================================================================
#   UPDATE JIRA ISSUES + ATTACH CERTIFICATES
#   Supports: status, comments, labels, story points, assignee, PDFs
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

# Directory where category/severity PDFs live
CERT_DIR = "/Users/michaelritchson/desktop/development/JIRA/certificates"


# ============================================================
# Attach PDF based on category + severity
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

    # Try each filename variation
    for fname in possible_filenames:
        path = os.path.join(CERT_DIR, fname)
        if os.path.exists(path):
            return upload_pdf(issue_key, path)

    print(f"[WARN] No PDF found for category={category}, severity={severity}")
    return False


def upload_pdf(issue_key, file_path):
    """
    Uploads a PDF to a Jira issue.
    """
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/attachments"

    headers = {"X-Atlassian-Token": "no-check"}

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        response = requests.post(url, headers=headers, auth=AUTH, files=files)

    if response.status_code == 200:
        print(f"[ATTACHED] {os.path.basename(file_path)} → {issue_key}")
        return True

    print(f"[ERROR] Failed to attach PDF to {issue_key}: {response.status_code} → {response.text}")
    return False


# ============================================================
# Jira Update Functions
# ============================================================
def update_status(issue_key, status):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions"
    # Fetch transitions
    transitions = requests.get(url, headers=HEADERS, auth=AUTH).json().get("transitions", [])

    # Find matching transition
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
                {"type": "paragraph", "content": [{"type": "text", "text": comment}]}
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

    # Grab your accountId
    me = requests.get(f"{JIRA_DOMAIN}/rest/api/3/myself", headers=HEADERS, auth=AUTH).json()
    acct = me["accountId"]

    r = requests.put(url, headers=HEADERS, auth=AUTH, json={"accountId": acct})
    print(f"[ASSIGNEE] {issue_key}: {r.status_code}")


def update_story_points(issue_key, points):
    # Detect Story Points field dynamically
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
# Batch Processor
# ============================================================
def process_rtm(path):
    with open(path, "r") as f:
        items = json.load(f)

    for entry in items:
        issue = entry["issue"]
        print(f"\n=== Updating {issue} ===")

        # Normal updates
        if "status" in entry:
            update_status(issue, entry["status"])

        if "comment" in entry:
            add_comment(issue, entry["comment"])

        assign_to_me(issue)

        if "labels" in entry:
            add_labels(issue, entry["labels"])

        if "points" in entry:
            update_story_points(issue, entry["points"])

        # PDF attachment logic
        category = entry.get("category")
        severity = entry.get("severity")

        if category and severity:
            attach_certificate(issue, category, severity)
        else:
            print(f"[INFO] No PDF attachment fields for {issue} (category/severity missing)")


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Update Jira issues and attach PDFs.")
    parser.add_argument("--rtm", required=True, help="JSON update file")

    args = parser.parse_args()
    process_rtm(args.rtm)


if __name__ == "__main__":
    main()
