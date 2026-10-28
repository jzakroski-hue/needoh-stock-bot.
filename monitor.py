import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

API_URL = "https://api.openwebninja.com/realtime-shopping-data"
API_KEY = os.environ.get("OPENWEBNINJA_API_KEY", "")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")


def load_config():
    with open("products.json", encoding="utf-8") as f:
        return json.load(f)


def money(value):
    if value is None or isinstance(value, bool):
        return None
    match = re.search(r"\d[\d,]*(?:\.\d+)?", str(value))
    if not match:
        return None
    try:
        return Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None


def eligible_title(title, cfg):
    name = str(title or "").casefold()
    if not ("needoh" in name or "nee doh" in name):
        return False
    if any(str(word).casefold() in name for word in cfg.get("excluded", [])):
        return False
    # Always exclude regular/original Fuzz Balls, irrespective of other rules.
    if "fuzz ball" in name or "fuzzball" in name:
        return False
    return True


def price_limit(title, cfg):
    name = title.casefold()
    for variety, limit in cfg.get("price_limits", {}).items():
        if str(variety).casefold() in name:
            return money(limit)
    return money(cfg.get("default_max_price", 10))


def verified_stock(product):
    # Only explicit positive inventory values count; missing status is unknown.
    value = str(product.get("availability") or "").strip().casefold()
    return value in {"in_stock", "in stock", "instock"}


def direct_product_url(product):
    url = str(product.get("product_page_url") or "").strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = (parsed.hostname or "").casefold()
    if host in {"google.com", "www.google.com", "shopping.google.com"} or host.endswith(".google.com"):
        return ""
    return url


def search_products():
    if not API_KEY:
        raise RuntimeError("OPENWEBNINJA_API_KEY secret is missing")
    params = urllib.parse.urlencode({"q": "Schylling NeeDoh", "country": "us", "limit": 40})
    req = urllib.request.Request(API_URL + "?" + params, headers={"x-api-key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as e:
        print("Shopping API HTTP error:", e.code)
        print("API response:", e.read().decode("utf-8", errors="replace")[:1500])
        raise
    products = payload.get("data", {}).get("products", [])
    if not isinstance(products, list):
        raise RuntimeError("Unexpected shopping API response: products is not a list")
    return products


def notify(message):
    if not NTFY_TOPIC:
        raise RuntimeError("NTFY_TOPIC secret is missing")
    req = urllib.request.Request(
        "https://ntfy.sh/" + urllib.parse.quote(NTFY_TOPIC, safe=""),
        data=message.encode("utf-8"),
        headers={"Title": "NeeDoh verified listing", "Tags": "shopping_cart"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        print("Notification status:", response.status)


def main():
    cfg = load_config()
    listings = search_products()
    print("Shopping listings returned:", len(listings))
    candidates = []
    unknown_stock = 0
    for item in listings:
        title = str(item.get("product_title") or "")
        if not eligible_title(title, cfg):
            continue
        price = money(item.get("price"))
        limit = price_limit(title, cfg)
        if price is None or limit is None or not (Decimal("0") < price <= limit):
            continue
        if not verified_stock(item):
            unknown_stock += 1
            continue
        url = direct_product_url(item)
        if not url:
            continue
        candidates.append((title, price, item.get("store_name", "Unknown store"), url))

    print("Price-qualified listings without explicit in-stock verification:", unknown_stock)
    print("Verified listings with direct links:", len(candidates))
    if not candidates:
        print("No verified stock alerts. Search results alone do not prove availability.")
        return
    # Do not auto-buy. Notify only; store confirmation is still needed.
    lines = ["NeeDoh listings reporting in-stock (confirm at retailer):"]
    for title, price, store, url in candidates[:10]:
        lines.append(f"{title} | ${price:.2f} | {store}\n{url}")
    notify("\n\n".join(lines))


if __name__ == "__main__":
    main()
