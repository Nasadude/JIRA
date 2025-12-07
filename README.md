# 📘 **Jira Automation Toolkit — README**

This repository contains a set of automation tools for managing Jira issues programmatically.
It supports **creating issues**, **updating existing issues**, **bulk operations**, and **attaching PDF certificates or other files** directly to Jira Cloud.

The scripts are designed to work with Jira Cloud REST API v3 and require only Python and a Jira API token.

---

# 🚀 **Features**

### 🔹 Create Jira Issues (Stories, Features, Epics, etc.)

* Create issues in batch using JSON input
* Automatically place issues under epics
* Set summary, description, labels, story points, and more

### 🔹 Update Existing Jira Issues

Supports bulk updates or single-issue updates for:

* Status transitions
* Comments
* Labels
* Story points
* Assignee
* Any combination of fields

### 🔹 Upload File Attachments

Attach one or more files (PDF, images, logs, etc.) to Jira issues.

Perfect for:

* Certificates
* Reports
* Test artifacts
* Logs and diagnostic files

### 🔹 JSON-Driven Workflows

All bulk operations are driven by JSON definition files, so you can maintain your Jira updates in source control and automate workflows easily.

---

# 📁 **Repository Structure**

```
/scripts
    create_jira.py        # Create new Jira issues
    update_jira.py        # Update existing issues / upload attachments

/certificates
    <your PDF files>      # Certificates or files to attach to issues

README.md                # This documentation
```

---

# 🔧 **Configuration**

Both scripts rely on a few environment variables:

```bash
export JIRA_API_TOKEN="your_token_here"
export JIRA_EMAIL="mike@technating.io"
export JIRA_DOMAIN="https://technating.atlassian.net"
```

You can store these in:

```
~/.zshrc
~/.bashrc
~/.bash_profile
```

Then reload:

```bash
source ~/.zshrc
```

---

# 📜 **1. Creating Jira Issues**

Use `create_jira.py` to generate new Jira issues from a JSON file.

### Example JSON:

```json
[
  {
    "epic": "CPG-10",
    "summary": "Upload Maneuver LOW Certificate",
    "description": "Automated creation of issue for certificate upload.",
    "issuetype": "Feature",
    "labels": ["certificate", "automation"]
  }
]
```

### Run:

```bash
python3 create_jira.py --file create_issues.json
```

---

# ✏️ **2. Updating Jira Issues**

Use `update_jira.py` to update status, comments, labels, points, and more.

### Example JSON:

```json
[
  {
    "issue": "CPG-97",
    "status": "To Do",
    "comment": "Attaching maneuver LOW certificate.",
    "labels": ["certificate", "maneuver"],
    "points": 1
  }
]
```

### Run:

```bash
python3 update_jira.py --rtm updates.json
```

---

# 📎 **3. Attaching Files (PDFs, Images, Reports)**

`update_jira.py` supports file attachments via two fields:

* `"category"`
* `"severity"`

These tell the script which file to upload.

### Example:

```json
[
  {
    "issue": "CPG-97",
    "comment": "Uploading maneuver LOW certificate.",
    "category": "maneuver",
    "severity": "LOW"
  }
]
```

Certificate directory:

```
/certificates
    maneuver_LOW.pdf
    maneuver_HIGH.pdf
    conjunction_CRITICAL.pdf
```

### Run:

```bash
python3 update_jira.py --rtm upload_files.json
```

---

# 🧪 **Testing Tips**

* Run with one issue first to verify the format
* Use `print` debugging inside the scripts if needed
* Jira may reject attachments if `"X-Atlassian-Token: no-check"` is missing — the script handles this automatically
* If an issue type fails, verify valid types via:

```bash
curl -u <email>:<token> \
  -X GET \
  "https://yourdomain.atlassian.net/rest/api/3/issuetype"
```

---

# 🛠️ **Extending the Toolkit**

This toolkit is designed to be easy to modify.

You can extend it to support:

* Sprint assignment
* Linking issues
* Creating subtasks
* Updating versions
* Automatically generating issues from templates
* Automated certificate pipelines

If you want, I can generate:

* A `Makefile` wrapper
* A CLI wrapper (`jira-cli`)
* A GitHub Actions automation workflow
* A version that signs PDF certificates before upload

---

If you'd like a **Confluence-friendly version**, **GitHub stylized version**, or a **CLI installer script**, I can generate those next.
