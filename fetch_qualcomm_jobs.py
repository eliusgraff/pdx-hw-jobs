import requests
from datetime import datetime, timezone
from helper import is_old, print_jobs

def fetch_qualcomm_jobs():
    url = "https://careers.qualcomm.com/api/pcsx/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
    }

    # Use a session to persist cookies across the two-step request flow
    s = requests.Session()
    s.headers.update(headers)

    # First get the careers page to establish cookies and CSRF token
    r = s.get("https://careers.qualcomm.com/careers?location=oregon")
    r.raise_for_status()
    # The CSRF token is passed back via response header and required for the API call
    csrf_token = r.headers.get("X-CSRF-Token", "")

    # Hit the PCSX search API with location filter
    r2 = s.get(url,
        params={
            "location": "Oregon",
            "num": 50,
            "domain": "qualcomm.com",
            "start": 0,
            "sort_by": "timestamp",
        },
        headers={
            "Accept": "application/json",
            "X-CSRF-Token": csrf_token,
        }
    )
    r2.raise_for_status()
    data = r2.json()

    all_jobs = []

    # Walk each position in the result set, filtering out old postings
    for pos in data["data"]["positions"]:
        posted_dt = datetime.fromtimestamp(pos["postedTs"], tz=timezone.utc)
        if is_old(posted_dt):
            continue
        posted_date = posted_dt.isoformat()

        job_deets = {
            "title": pos["name"],
            "id": pos["displayJobId"],
            "post_date": posted_date,
            "url": "https://careers.qualcomm.com" + pos["positionUrl"],
            "location": ", ".join(pos["locations"]),
            "department": pos.get("department", ""),
        }

        all_jobs.append(job_deets)

    return all_jobs


if __name__ == "__main__":
    print_jobs(fetch_qualcomm_jobs())
