
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

TOPIC = os.environ.get("NTFY_TOPIC", "").strip()

EXCLUDED = [
    "nice cube", "dream drop", "gumdrop",
    "color changing", "color-changing",
    "cool cats", "mello mallo"
]

SEARCHES = {
    "Amazon": "site:amazon.com Schylling NeeDoh",
    "Walmart": "site:walmart.com Schylling NeeDoh",
    "Target": "site:target.com Schylling NeeDoh"
}

def eligible(title):
    name = title.lower()
    if any(word in name for word in EXCLUDED):
        return False
    if "fuzz" in name and "original fuzz" not in name:
        return False
    return "needoh" in name or "nee doh" in name

def send_alert(message):
    if not TOPIC:
        raise RuntimeError("NTFY_TOPIC is missing")
    req = urllib.request.Request(
        "https://ntfy.sh/" + TOPIC,
        data=message.encode("utf-8"),
        headers={"Title": "NeeDoh Shopping Results"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        print("Notification HTTP status:", r.status)

def main():
    results = []
    for store, query in SEARCHES.items():
        url = (
            "https://www.google.com/search?tbm=shop&q="
            + urllib.parse.quote(query)
        )
        results.append(store + ": " + url)

    message = (
        "NeeDoh shopping searches are ready.\n"
        "These links are NOT confirmed in-stock items.\n\n"
        + "\n".join(results)
        + "\n\nBudget: $300. Manual purchase only."
    )
    print(message)
    send_alert(message)

if __name__ == "__main__":
    main()
