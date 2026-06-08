import requests
import json
from bs4 import BeautifulSoup
from html import unescape
from datetime import datetime
from helper import print_jobs

BASE_URL = "https://careers.nearfieldinstruments.com"

def fetch_nfi_jobs():
    url = f"{BASE_URL}/jobs?jobs-f1082b85[country][]=US"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    if not r.text:
        return []

    # The page embeds all job data as HTML-entity-encoded JSON in the data-props
    # attribute of the single div that carries the data-rendered marker
    soup = BeautifulSoup(r.text, 'html.parser')
    rendered_tag = soup.find(attrs={"data-rendered": True})
    if not rendered_tag:
        print("Error: could not find data-rendered tag")
        return []

    raw_props = rendered_tag.get("data-props", "")
    data = json.loads(unescape(raw_props))

    # Recursively walk the decoded object to locate the offers list
    def find_key(obj, target, depth=0):
        if depth > 6:
            return None
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == target:
                    return v
                result = find_key(v, target, depth + 1)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_key(item, target, depth + 1)
                if result is not None:
                    return result
        return None

    offers = find_key(data, "offers") or []

    # The data-props JSON omits post dates, so fetch them from the public Recruitee API.
    # Build a map of offer id -> published_at datetime for fast lookup.
    published_map = {}
    try:
        api_url = "https://nearfieldinstruments1.recruitee.com/api/offers/?country_code=US"
        api_r = requests.get(api_url, timeout=10)
        api_r.raise_for_status()
        for api_offer in api_r.json().get("offers", []):
            raw_date = api_offer.get("published_at")
            if raw_date:
                # Format: "2026-06-03 12:38:31 UTC"
                published_map[api_offer["slug"]] = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        print(f"Warning: could not fetch post dates from Recruitee API: {e}")

    all_jobs = []
    for offer in offers:
        # The URL already filtered to US, but guard in case the full list is returned
        if offer.get("countryCode") != "US":
            continue

        en = offer.get("translations", {}).get("en", {})
        title = en.get("title")
        slug  = offer.get("slug")
        city  = offer.get("city")
        state = en.get("state")

        location_parts = [p for p in [city, state] if p]
        location = ", ".join(location_parts) if location_parts else None
        job_url = f"{BASE_URL}/o/{slug}" if slug else None

        all_jobs.append({
            "id":        str(offer["id"]) if offer.get("id") is not None else None,
            "title":     title,
            "location":  location,
            "url":       job_url,
            "post_date": published_map.get(slug),
        })

    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_nfi_jobs())