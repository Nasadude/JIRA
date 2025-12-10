import requests

domain = "https://technating.atlassian.net"
email = "mike@technating.io"
token = "<YOUR_API_TOKEN>"

r = requests.get(
    f"{domain}/rest/api/3/project/search",
    auth=(email, token),
    headers={"Accept": "application/json"}
)

print(r.status_code)
print(r.json())
