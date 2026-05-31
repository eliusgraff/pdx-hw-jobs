import requests
from datetime import datetime, timedelta
import re
import time
from helper import is_old, print_jobs

def resolve_locations(external_path, headers):
    """Fetch the full list of locations for a job posting from the  detail API."""
    detail_url = f"https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext{external_path}"
    try:
        response = requests.get(detail_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        job_posting_info = data.get("jobPostingInfo", {})
        primary = job_posting_info.get("location", "")
        additional = job_posting_info.get("additionalLocations", [])
        all_locations = [primary] + additional if primary else additional
        if all_locations:
            return ", ".join(all_locations)
    except requests.exceptions.RequestException as e:
        pass
    
    return None


def fetch_autodesk_jobs():
    base_url = "https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext/jobs"
    
    # This payload is derived from the user's provided JSON
    payload = {
        "appliedFacets":{
            "locations":[
                "33c9184ffc6401eaa6e2e84a63015d42",
                "33c9184ffc64014a8740f92863014541",
                "33c9184ffc6401d850e7a34a63013042",
                "5dbd45c76ba901c6435d3ef27b98d278",
                "01ba61f9692f44daaf4ce8b08254179c"
            ],
            "jobFamilyGroup":[
                "1f75c4299c9201c0f3b5f8e6fa01c5bf",
                "618805f018ad0121295e43c1fa011ebd",
                "6bf025de66fd100072a01a45a07d0000"
            ]
        },
        "limit":20,
        "offset":0,
        "searchText":""
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://autodesk.wd1.myworkdayjobs.com/en-US/Ext/details/Mid-Market-Construction-Sales-Executive_25WD92802?locations=33c9184ffc6401eaa6e2e84a63015d42&locations=33c9184ffc64014a8740f92863014541&locations=33c9184ffc6401d850e7a34a63013042&locations=5dbd45c76ba901c6435d3ef27b98d278&locations=01ba61f9692f44daaf4ce8b08254179c&jobFamilyGroup=1f75c4299c9201c0f3b5f8e6fa01c5bf&jobFamilyGroup=618805f018ad0121295e43c1fa011ebd&jobFamilyGroup=6bf025de66fd100072a01a45a07d0000",
        "Origin":"https://autodesk.wd1.myworkdayjobs.com"
    }
    
    all_jobs = []
    start = 0
    # Initialized to 1 so the while loop is entered on the first pass
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
                "location": job_tag.get("locationsText", job_tag.get("cityState")) ,
                "post_date":job_tag.get("postedOn"),
                "url":job_tag.get("externalPath"),
                "id": job_tag.get("bulletFields")
            }

            #Pulling job id out if it is found
            job_info['id'] = job_info['id'][0] if job_info['id'] != None else None

            #Adding full path to the external path if it was found
            raw_external_path = job_info['url']
            job_info['url'] = f"https://autodesk.wd1.myworkdayjobs.com/en-US/Ext{raw_external_path}" if raw_external_path != None else None

            # If the location just says 'X Locations', resolve the actual names
            if "Locations" in str(job_info['location']) and raw_external_path != None:
                resolved = resolve_locations(raw_external_path, headers)
                if resolved:
                    job_info['location'] = resolved
                time.sleep(0.1)  # Be polite with detail requests
            
            #Turning 'Posted X Days Ago' into an actual date
            posted_str = job_info['post_date']
            parsed_date = datetime.now()
            
            num_days = re.search(r'\d+', posted_str)
            if num_days:
                parsed_date = datetime.now() - timedelta(days=int(num_days.group()))
                
                # 'Posted 30+ Days Ago' is imprecise; fetch the exact date from the job detail endpoint
                if "30+" in posted_str and raw_external_path != "Not Found...":
                    # Fetch the exact date from the internal API
                    try:
                        detail_url = f"https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext{raw_external_path}"
                        detail_resp = requests.get(detail_url, headers=headers)
                        if detail_resp.status_code == 200:
                            exact_date_str = detail_resp.json().get("jobPostingInfo", {}).get("startDate")
                            if exact_date_str:
                                parsed_date = datetime.strptime(exact_date_str, "%Y-%m-%d")
                    except Exception:
                        pass
            elif "Yesterday" in posted_str or "yesterday" in posted_str:
                parsed_date = datetime.now() - timedelta(days=1)
            
            job_info['post_date'] = parsed_date
            
            all_jobs.append(job_info)

        start += page_size

    # Sort all jobs by their posted date, most recent first
    all_jobs.sort(key=lambda x: x["post_date"], reverse=True)

    return all_jobs
    
if __name__ == "__main__":
    print_jobs(fetch_autodesk_jobs())