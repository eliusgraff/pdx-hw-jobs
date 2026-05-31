import requests
import time
import re
from datetime import datetime, timedelta
from helper import is_old, print_jobs


def fetch_intel_jobs():
    
    url = "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Origin": "https://intel.wd1.myworkdayjobs.com",
        "Referer": "https://intel.wd1.myworkdayjobs.com/en-US/External?locations=0741efd9f02e01994a3c9ca2ae078199&locations=1e4a4eb3adf1011246675c76bf81f8ce"
    }
    
    # These are the location IDs for Portland and Hillsboro from the user's URL
    location_ids = [
        "0741efd9f02e01994a3c9ca2ae078199",
        "1e4a4eb3adf1011246675c76bf81f8ce"
    ]

    # These are the IDs for the job types I'm looking for
    job_families =[
        "c37a9eaa90371000c6fd2261025d0000",
        "ace7a3d23b7e01a0544279031a0ec85c",
        "dc8bf79476611087d67b5159c64a703c",
        "c37a9eaa90371000c6fd29069de10000",
        "f31a130ea31c1000c6fd81ebbafd0000"
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
                "locations": location_ids,
                "jobFamilyGroup": job_families
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
                #print(f"Total jobs found: {total}")
            
            job_postings = data.get("jobPostings", [])
            for job in job_postings:
                # Construct the full URL
                external_path = job.get("externalPath", "")
                full_url = f"https://intel.wd1.myworkdayjobs.com/en-US/External{external_path}"
                
                #parse how many days ago this job was posted and turn that into a datetime for storage
                posted_str = job.get("postedOn", "")
                parsed_date = datetime.now()
                
                num_days_match = re.search(r'\d+', posted_str)
                if num_days_match:
                    num_days = int(num_days_match.group())
                    parsed_date = datetime.now() - timedelta(days=num_days)
                    
                    # '30+ days ago' is too vague; hit the job detail endpoint for an exact date
                    if "30+" in posted_str:
                        # Fetch the exact date from the job's internal API since 30+ isn't precise enough
                        try:
                            detail_url = f"https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External{external_path}"
                            detail_resp = requests.get(detail_url, headers={"Accept": "application/json", "User-Agent": headers["User-Agent"]})
                            if detail_resp.status_code == 200:
                                exact_date_str = detail_resp.json().get("jobPostingInfo", {}).get("startDate")
                                if exact_date_str:
                                    parsed_date = datetime.strptime(exact_date_str, "%Y-%m-%d")
                        
                        except Exception:
                            #I need to be more specific here
                            pass

                elif "Yesterday" in posted_str or "yesterday" in posted_str:
                    parsed_date = datetime.now() - timedelta(days=1)

                job_info = {
                    "id": job.get("bulletFields", [None])[0], # Often contains the Req ID
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
            break
            
    # Sort all jobs by their posted date, most recent first
    all_jobs.sort(key=lambda x: x["post_date"], reverse=True)
    
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_intel_jobs())

