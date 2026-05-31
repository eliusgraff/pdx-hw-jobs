import requests
import time
import re
from datetime import datetime, timedelta
from helper import is_old, print_jobs


def fetch_kla_jobs():
    url = "https://kla.wd1.myworkdayjobs.com/wday/cxs/kla/Search/jobs"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Origin": "https://kla.wd1.myworkdayjobs.com",
        "Referer": "https://kla.wd1.myworkdayjobs.com/Search?Country=bc33aa3152ec42d4995f4791a106ed09&_gl=1*ul2vvf*_ga*NjYxNzQ0OTc1LjE3Njc1NjE4NDA.*_ga_TZPEFM1MF5*czE3NzUzNTQ0MzckbzUkZzEkdDE3NzUzNTQ0NDgkajQ5JGwwJGgw&_ga=2.57455274.1038409659.1775354438-661744975.1767561840&State_Province_Region=6fcc4198762c4a7c807486c849fe94dd"

    }
    
    # These are the location IDs for Portland and Hillsboro from the user's URL
    country_id = [
        "bc33aa3152ec42d4995f4791a106ed09"
    ]

    # These are the IDs for the job types I'm looking for
    state_province_region_id =[
        "6fcc4198762c4a7c807486c849fe94dd"
    ]
    
    all_jobs = []
    # Number of results to request per API call
    limit = 20
    offset = 0
    # Initialized to 1 so the while loop is entered on the first pass
    total = 1 # Initial value to start the loop
        
    # Paginate until all jobs have been retrieved
    while offset < total:
        payload = {
            "appliedFacets": {
                "Country": country_id,
                "State_Province_Region": state_province_region_id
            },

            "limit": limit,
            "offset": offset,
            "searchText": ""
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Update total on the first request
            if offset == 0:
                total = data.get("total", 0)
            
            job_postings = data.get("jobPostings", [])
            for job in job_postings:
                # Construct the full URL
                external_path = job.get("externalPath", "")
                full_url = f"https://kla.wd1.myworkdayjobs.com/en-US/Search{external_path}"
                
                posted_str = job.get("postedOn", "")
                parsed_date = datetime.now()
                
                num_days_match = re.search(r'\d+', posted_str)
                if num_days_match:
                    num_days = int(num_days_match.group())
                    parsed_date = datetime.now() - timedelta(days=num_days)
                    
                    # '30+ days ago' is too vague; hit the job detail endpoint for an exact date
                    if "30+" in posted_str:
                        try:
                            
                            detail_url = f"https://kla.wd1.myworkdayjobs.com/wday/cxs/kla/Search{external_path}"
                            detail_resp = requests.get(detail_url, headers={"Accept": "application/json", "User-Agent": headers["User-Agent"]})
                            
                            if detail_resp.status_code == 200:
                                exact_date_str = detail_resp.json().get("jobPostingInfo", {}).get("startDate")
                                
                                if exact_date_str:
                                    parsed_date = datetime.strptime(exact_date_str, "%Y-%m-%d")
                        
                        except Exception:
                            #I should be more specific here
                            pass
                
                #make and educated guessif the actual date is not given
                elif "Yesterday" in posted_str or "yesterday" in posted_str:
                    parsed_date = datetime.now() - timedelta(days=1)

                job_info = {
                    "id": job.get("bulletFields", [None])[0] if job.get("bulletFields") else None,
                    "title": job.get("title"),
                    "location": job.get("locationsText"),
                    "post_date": parsed_date,
                    "url": full_url
                }
                all_jobs.append(job_info)
                
            offset += limit
            # Avoid hitting the API too fast
            if offset < total:
                time.sleep(0.1)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs: {e}")
            break
            
    
    # Sort since Workday's POST API doesn't support date sorting
    all_jobs.sort(key=lambda x: x["post_date"], reverse=True)
    
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_kla_jobs())
