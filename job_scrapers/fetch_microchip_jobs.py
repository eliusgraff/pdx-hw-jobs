import requests
from datetime import datetime, timedelta
import re
import time
from helper import is_old, print_jobs

def resolve_details(external_path, headers):
    """Fetch the full list of locations for a job posting from the Workday detail API."""
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
            
            job_info = {
                "title": job_tag.get("title"),
                "location": job_tag.get("locationsText") ,
                "post_date":job_tag.get("postedOn"),
                "url":job_tag.get("externalPath"),
                "job_id": job_tag.get("bulletFields")
            }

            #Pulling job id out if it is found
            job_info['job_id'] = job_info['job_id'][0] if job_info['job_id'] != None else None

            #Adding full path to the external path if it was found
            raw_external_path = job_info['url']
            job_info['url'] = f"https://wd5.myworkdaysite.com/en-US/recruiting/microchiphr/External{job_info['url']}" if job_info['url'] != None else None

            #Turning 'Posted X Days Ago' into an actual date
            raw_date = job_info['post_date']
            num_days = re.search(r'\d+', job_info['post_date'])
            if num_days:
                temp_dt = datetime.now() - timedelta(days=int(num_days.group()))
                job_info['post_date'] = temp_dt

            # If the location just says 'X Locations', resolve the actual names
            if "Locations" in job_info['location'] or "30+" in raw_date and raw_external_path != None:
                time.sleep(0.1)  # Be polite with detail requests
                resolved = resolve_details(raw_external_path, headers)
                for key, value in resolved.items():
                    job_info[key] = value
            
            all_jobs.append(job_info)

        # Stop paging once the oldest job on the current page exceeds our threshold
        if is_old(all_jobs[-1]['post_date']):
            return all_jobs

        start += page_size

    return all_jobs
    
if __name__ == "__main__":
    print_jobs(fetch_microchip_jobs())
