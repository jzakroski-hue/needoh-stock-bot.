import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
API_KEY = os.environ.get("OPENWEBNINJA_API_KEY", "")
API_URL = "https://api.openwebninja.com/realtime-product-search/search"
with open("products.json", "r", encoding="utf-8") as file:
    CONFIG = json.load(file)
ZIP_CODE = CONFIG["zip_code"]
RADIUS_MILES = CONFIG["radius_miles"]
EXCLUDED = CONFIG["excluded"]
MAX_TOTAL_BUDGET = CONFIG["max_total_budget"]
PRICE_LIMITS = CONFIG["price_limits"]
DEFAULT_MAX_PRICE = CONFIG["default_max_price"]
FUZZBALLS_RULE = CONFIG["fuzzballs_rule"]
# SEARCHES = {
    # "Amazon": "site:amazon.com Schylling NeeDoh",
    # "Walmart": "site:walmart.com Schylling NeeDoh 21231",
    # "Target": "site:target.com Schylling NeeDoh 21231"
#}
SEARCHES = {}
def eligible(title):
    name = title.lower()
    if any(word in name for word in EXCLUDED):
        return False
        if FUZZBALLS_RULE == "exclude_all" and ("fuzz" in name or "fuzzball" in name):
            return False
    return "needoh" in name or "nee doh" in name
def get_price_limit(title):
    name = title.lower()
    for variety, limit in PRICE_LIMITS.items():
        if variety in name:
            return limit
    return DEFAULT_MAX_PRICE
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

def search_products():
        if not API_KEY:
            raise RuntimeError("OpenWeb Ninja API key is missing")
        params = {"q": "Schylling NeeDoh", "country": "us", "stores": "amazon,walmart,target", "limit": 40}
        url = API_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.load(response)
        return data.get("data", {}).get("products", [])
def main():
        products = search_products()
        products = [p for p in products if eligible(p.get("product_title", ""))]
        print("Eligible products found:", len(products))
        # print("FIRST PRODUCT:", json.dumps(products[0], indent=2))
        message = f"NeeDoh API search returned {len(products)} products. Stock and prices are not yet verified."
        print(message)
        # send_alert(message)

if __name__ == "__main__":
    main()
