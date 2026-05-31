import requests
import time
from datetime import datetime
from helper import is_old, print_jobs


def fetch_microsoft_jobs():

    base_url = "https://apply.careers.microsoft.com/api/pcsx/search"
    params = {
        "domain": "microsoft.com",
        "location": "oregon",
        "start": 0,
        "sort_by": "timestamp",
        "filter_include_remote": 1,
        "filter_distance" : 100,
        "filter_seniority": ["Senior","Mid-Level","Manager","Director"]
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    
    all_jobs = []
    start = 0
    # Initialized to 1 so the while loop runs at least once
    total = 1 # Initial value to start the loop
    # API seems to return 10 results per page
    page_size = 10 # API seems to return 10 items per request
        
    # Paginate until all available jobs are fetched
    while start < total:
        params["start"] = start
        
        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            break

        data = response.json()
        
        result_data = data.get("data", {})
        
        # Update total on the first request
        if start == 0:
            total = result_data.get("count", 0)
        
        positions = result_data.get("positions", [])
        # Normalize each raw position record into our standard dictionary
        for job in positions:
            # Standardized data extraction
            job_id = job.get("displayJobId") or job.get("id")
            title = job.get("name")
            locations = job.get("standardizedLocations", [])
            posted_ts = job.get("postedTs")
            department = job.get("department")
            
            # Format posted date
            posted_date = datetime.fromtimestamp(posted_ts).strftime('%Y-%m-%d') if posted_ts else None
            
            # Construct the full URL
            position_url = job.get("positionUrl")
            full_url = f"https://apply.careers.microsoft.com{position_url}" if position_url is not None else None
            
            job_info = {
                "id": job_id,
                "title": title,
                "location": ", ".join(locations) if isinstance(locations, list) else locations,
                "post_date": posted_date,
                "url": full_url,
                "department": department
            }
            all_jobs.append(job_info)
        
        last_job_date = datetime.fromtimestamp(positions[-1]["postedTs"])

        # Stop paging once the last job on the page exceeds our age threshold
        if is_old(last_job_date):
            break

        start += page_size
        # Avoid hitting the API too fast
        if start < total:
            time.sleep(0.5)
            
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_microsoft_jobs())
