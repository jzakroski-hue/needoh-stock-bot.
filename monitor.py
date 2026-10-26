import os
import urllib.request

print("NeeDoh notification test starting...")

topic = os.environ.get("NTFY_TOPIC", "")
if not topic:
    raise RuntimeError("NTFY_TOPIC is missing from GitHub Secrets")

url = "https://ntfy.sh/" + topic
message = "Success! Your NeeDoh GitHub bot can send alerts to your Samsung S23."

request = urllib.request.Request(
    url,
    data=message.encode("utf-8"),
    headers={"Title": "NeeDoh Bot Test", "Tags": "white_check_mark"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=20) as response:
    print("Notification sent. HTTP status:", response.status)
