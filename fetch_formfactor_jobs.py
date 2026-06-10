import requests
import time
import re
from datetime import datetime, timedelta
from helper import is_old, print_jobs

def parse_workday_date(posted_str):
    if not posted_str:
        return datetime.now()
        
    posted_str = posted_str.lower()
    
    if "today" in posted_str:
        return datetime.now()
    elif "yesterday" in posted_str:
        return datetime.now() - timedelta(days=1)
    elif "days ago" in posted_str:
        match = re.search(r'(\d+)', posted_str)
        if match:
            days = int(match.group(1))
            return datetime.now() - timedelta(days=days)
            
    # Default fallback
    return datetime.now()

def fetch_formfactor_jobs():
    base_url = "https://formfactor.wd1.myworkdayjobs.com/wday/cxs/formfactor/FFI-Careers/jobs"
    
    payload = {
        "appliedFacets": {
            "locations": ["04656ce6e7671001fc0502f65ac90000", "1d883335cd9f1001fb98b2a95ee40000"]
        },
        "limit": 20,
        "offset": 0,
        "searchText": ""
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
    }
    
    all_jobs = []
    start = 0
    total = 1
    page_size = 20
    
    while start < total:
        payload["offset"] = start
        
        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs: {e}")
            break
            
        data = response.json()
        
        if start == 0:
            total = data.get("total", 0)
            
        jobs_list = data.get("jobPostings", [])
        
        for job in jobs_list:
            # bulletFields usually contains the req ID in Workday
            req_id = ""
            if job.get("bulletFields"):
                req_id = job["bulletFields"][0]
                
            external_path = job.get("externalPath", "")
            full_url = f"https://formfactor.wd1.myworkdayjobs.com/en-US/FFI-Careers{external_path}"
            
            # The ID can also be extracted from the end of externalPath
            job_id = external_path.split("_")[-1] if "_" in external_path else req_id
            
            title = job.get("title", "")
            location = job.get("locationsText", "")
            
            posted_str = job.get("postedOn", "")
            post_date = parse_workday_date(posted_str)
            
            job_info = {
                "id": job_id,
                "title": title,
                "location": location,
                "post_date": post_date,
                "url": full_url
            }
            
            all_jobs.append(job_info)
            
        start += page_size
        time.sleep(0.1)
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_formfactor_jobs())
