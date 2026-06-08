import requests
from datetime import datetime, timedelta
import re
import time
from helper import is_old, print_jobs

#Turn strings "Posted X days ago" into a datetime
def posted_to_dt(posted_str):
    s = posted_str.strip().lower()
    if "yesterday" in s:
        return datetime.now() - timedelta(days=1)
    elif "today" in s:
        return datetime.now()
    elif "30+" in s:
        return datetime.now() - timedelta(days=30)
        
    match = re.search(r'(\d+)\s+day', s)
    if match:
        return datetime.now() - timedelta(days=int(match.group(1)))

    return None

#Fetch the full list of locations for a job posting from the Workday detail API.
def resolve_details(external_path, headers):
    target_url = f"https://wd5.myworkdaysite.com/wday/cxs/microchiphr/External{external_path}"

    job_deets = {}

    try:
        response = requests.get(target_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        job_posting_info = data.get("jobPostingInfo", {})
        primary = job_posting_info.get("location", "")
        additional = job_posting_info.get("additionalLocations", [])
        all_locations = [primary] + additional if primary else additional
        if all_locations:
            job_deets["location"] = ", ".join(all_locations)
        
        start_date = job_posting_info.get("startDate")
        if start_date is not None:
            job_deets["postedDate"] = datetime.strptime(start_date, "%Y-%m-%d")

    except requests.exceptions.RequestException as e:
        pass

    return job_deets


def fetch_microchip_jobs():
    base_url = "https://wd5.myworkdaysite.com/wday/cxs/microchiphr/External/jobs"
    
    #Send post request and share filters as json
    payload = {
        "appliedFacets":{
            "locations":[
                "8f5c306c848501f5b8dd24b48e12064c",
                "97054e5be3aa10080ae4fc50603323ca"
            ],
            "timeType":[
                "51c161e7620310f46a28a73d306c1426"
                ]},
            "limit":20,
            "offset":0,
            "searchText":""
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://wd5.myworkdaysite.com/en-US/recruiting/microchiphr/External?locations=8f5c306c848501f5b8dd24b48e12064c&locations=97054e5be3aa10080ae4fc50603323ca&timeType=51c161e7620310f46a28a73d306c1426",
        "Origin":"https://wd5.myworkdaysite.com"
    }
    
    all_jobs = []
    start = 0
    # Initialized to 1 so the while loop runs at least once
    total = 1 # Initial value to start the loop
    # Number of results requested per API call
    page_size = 20 # In case more than 10 jobs pop up, page through 10 at a time
        
    # Paginate until all jobs have been retrieved
    while start < total:
        
        payload["offset"] = start
        try:
            response = requests.post(base_url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            break
        
        data = response.json()
        
        # Update total only on the first request
        if start == 0:
            total = data["total"]
        else:
            #Avoid spamming API on any subsequent requests
            time.sleep(1)

        jobs_list = data.get("jobPostings",[])

        for job_tag in jobs_list:

            try:
                job_id = job_tag["bulletFields"][0]
            except KeyError:
                job_id = None
            except IndexError:
                job_id = None
            
            job_info = {
                "title": job_tag.get("title"),
                "location": job_tag.get("locationsText") ,
                "post_date": posted_to_dt(job_tag["postedOn"]) if job_tag.get("postedOn") is not None else None,
                "url":f"https://wd5.myworkdaysite.com/en-US/recruiting/microchiphr/External{job_tag.get("externalPath")}" if job_tag.get("externalPath") != None else None,
                "id": job_id
            }
            
            all_jobs.append(job_info)

        start += page_size

    return all_jobs
    
if __name__ == "__main__":
    print_jobs(fetch_microchip_jobs())
