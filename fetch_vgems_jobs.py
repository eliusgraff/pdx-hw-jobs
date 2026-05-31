import requests
from datetime import datetime
from helper import is_old, print_jobs



def fetch_vgems_jobs():
    url = "https://apply.workable.com/api/v3/accounts/vanguard-ems-inc/jobs"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    request_payload = {
        "query":"",
        "department":[],
        "location":
        [
            {"country":"United States",
            "region":"Oregon",
            "city":"Beaverton",
            "countryCode":"US"
            }
        ],
        "workplace":[],
        "worktype":[]
    }

    r = requests.post(url, headers=headers, json=request_payload)
    r.raise_for_status()
    data = r.json()

    all_jobs = []

    # Walk each job record and build a normalized dictionary
    for job in data["results"]:
        # Parse the ISO 8601 publish date and check if it's within our threshold
        posted_dt = job.get("published")
        if posted_dt:
            posted_dt = datetime.fromisoformat(posted_dt.replace("Z", "+00:00")).replace(tzinfo=None)
            # Workable returns jobs newest-first; stop as soon as we hit an old one
            if is_old(posted_dt):
                return all_jobs

        job_deets = {
            "title": job["title"],
            "id": job.get("code"),
            "post_date": posted_dt,
            "url": f"https://apply.workable.com/vanguard-ems-inc/j/{job['shortcode']}/",
            "location": f"{job['location'].get('city', '')}, {job['location'].get('region', '')}",
            "department": ", ".join(job.get("department", [])),
        }

        all_jobs.append(job_deets)

    return all_jobs


if __name__ == "__main__":
    print_jobs(fetch_vgems_jobs())
