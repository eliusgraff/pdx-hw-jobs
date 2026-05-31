import requests
from datetime import datetime, timezone
from helper import is_old, print_jobs
import time

BASE_URL = "https://careers.appliedmaterials.com"
SEARCH_URL = f"{BASE_URL}/api/pcsx/search"

def fetch_amat_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://careers.appliedmaterials.com/careers/search",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    params = {
        "domain": "appliedmaterials.com",
        "query": "",
        "location": "oregon",
        "sort_by": "timestamp",
        "filter_include_remote": "1",
        "filter_country": "United States of America",
    }

    all_jobs = []
    start = 0
    # Number of results returned per API page (Applied Materials default)
    page_size = 25  # default page size returned by API
    total_count = None

    # Keep requesting pages until all jobs are fetched or we hit old postings
    while True:
        params["start"] = start
        r = requests.get(SEARCH_URL, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()

        positions = data["data"]["positions"]
        if total_count is None:
            # Capture total job count from the first response to drive pagination
            total_count = data["data"]["count"]
            #print(f"Total jobs found: {total_count}")

        # Stop early if the page came back empty
        if not positions:
            break

        # Extract the standardized fields we care about from each job record
        for pos in positions:
            posted_ts = pos.get("postedTs")
            posted_date = (
                datetime.fromtimestamp(posted_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                if posted_ts
                else None
            )

            job_deets = {
                "title": pos.get("name"),
                "id": pos.get("displayJobId"),
                "location": ", ".join(pos.get("locations")) if pos.get("locations") else None,
                "department": pos.get("department"),
                "post_date": posted_date,
                "work_location_option": pos.get("workLocationOption"),
                "url": BASE_URL + pos.get("positionUrl", ""),
            }

            all_jobs.append(job_deets)

        start += len(positions)

        # Drop jobs older than 6 months
        if all_jobs:
            last_posted = all_jobs[-1]["post_date"]
            if last_posted:
                last_date = datetime.fromisoformat(last_posted)
                # Stop paging once the oldest job on the current page exceeds the age threshold
                if is_old(last_date):
                    #print("Reached jobs older than 6 months, stopping.")
                    break

        # Stop once we've fetched every available job
        if start >= total_count:
            break

        time.sleep(2)

    return all_jobs


if __name__ == "__main__":
    print_jobs(fetch_amat_jobs())