import requests
from datetime import datetime, timedelta
import json
import re
import time
from helper import is_old, print_jobs

def resolve_locations(external_path, headers):
    """Fetch the full list of locations for a job posting from the  detail API."""
    # The detail API endpoint mirrors the external path but under /wday/cxs/
    detail_url = f"https://analogdevices.wd1.myworkdayjobs.com/wday/cxs/analogdevices/External{external_path}"
    try:
        response = requests.get(detail_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Primary location is a string; additional locations is a list of strings
        job_posting_info = data.get("jobPostingInfo", {})
        primary = job_posting_info.get("location", "")
        additional = job_posting_info.get("additionalLocations", [])
        all_locations = [primary] + additional if primary else additional
        if all_locations:
            return ", ".join(all_locations)
    except requests.exceptions.RequestException as e:
        #print(f"  Warning: could not resolve locations: {e}")
        pass
    return None


def fetch_analog_devices_jobs():
    base_url = "https://analogdevices.wd1.myworkdayjobs.com/wday/cxs/analogdevices/External/jobs"
    
    # This payload is derived from the URL provided by the user
    payload = {
        "appliedFacets": {
            "jobFamilyGroup": [
                "633b03df4f5d1000ec24734fbbbb0000",
                "633b03df4f5d1000ec247e24e03b0000",
                "633b03df4f5d1000ec243f6e4cb40001",
                "d7b302590627100dddeb034354610000",
                "633b03df4f5d1000ec247955c4c40002"
            ],
            "locations": [
                "633b03df4f5d1000e7e6b905b2c60000",
                "633b03df4f5d1000e7e6d8f452240000"
            ]
        },
        "limit": 20,
        "offset": 0,
        "searchText": ""
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://analogdevices.wd1.myworkdayjobs.com/External?jobFamilyGroup=633b03df4f5d1000ec24734fbbbb0000&jobFamilyGroup=633b03df4f5d1000ec247e24e03b0000&jobFamilyGroup=633b03df4f5d1000ec243f6e4cb40001&jobFamilyGroup=d7b302590627100dddeb034354610000&jobFamilyGroup=633b03df4f5d1000ec247955c4c40002&locations=633b03df4f5d1000e7e6b905b2c60000&locations=633b03df4f5d1000e7e6d8f452240000",
        "Origin": "https://analogdevices.wd1.myworkdayjobs.com"
    }
    
    all_jobs = []
    start = 0
    # Initialized to 1 so the while loop is entered on the first pass
    total = 1 # Initial value to start the loop
    # Number of results requested per API call
    page_size = 20
        
    # Paginate until all jobs have been retrieved
    while start < total:
        
        payload["offset"] = start
        try:
            response = requests.post(base_url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            #print(f"Error fetching jobs: {e}")
            break
        
        data = response.json()
        
        # Update total only on the first request
        if start == 0:
            total = data.get("total", 0)
            if total == 0:
                break
        else:
            # Avoid spamming API on any subsequent requests
            time.sleep(1)

        jobs_list = data.get("jobPostings", [])

        for job_tag in jobs_list:
            
            job_info = {
                "title": job_tag.get("title"),
                "location": job_tag.get("locationsText", job_tag.get("cityState")) ,
                "post_date": job_tag.get("postedOn"),
                "url": job_tag.get("externalPath"),
                "id": job_tag.get("bulletFields")
            }

            # Pulling job id out if it is found (usually index 0 in bulletFields)
            if isinstance(job_info['id'], list) and len(job_info['id']) > 0:
                job_info['id'] = job_info['id'][0]
            else:
                job_info['id'] = None

            # Adding full path to the external path if it was found
            raw_external_path = job_info['url']
            if raw_external_path != "Not Found...":
                job_info['url'] = f"https://analogdevices.wd1.myworkdayjobs.com/en-US/External{raw_external_path}"

            # If the location just says 'X Locations', resolve the actual names
            if "Locations" in str(job_info['location']):
                resolved = resolve_locations(raw_external_path, headers)
                if resolved:
                    job_info['location'] = resolved
                time.sleep(0.2)  # Be polite with detail requests
            
            # Turning 'Posted X Days Ago' into an actual date
            posted_str = job_info['post_date']
            parsed_date = datetime.now()

            num_days_match = re.search(r'\d+', posted_str)
            if num_days_match:
                num_days = int(num_days_match.group())
                parsed_date = datetime.now() - timedelta(days=num_days)

                # 'Posted 30+ Days Ago' is imprecise; fetch the exact date from the job detail endpoint
                if "30+" in posted_str and raw_external_path != "Not Found...":
                    # Fetch the exact date from the internal API
                    try:
                        detail_url = f"https://analogdevices.wd1.myworkdayjobs.com/wday/cxs/analogdevices/External{raw_external_path}"
                        detail_resp = requests.get(detail_url, headers={"Accept": "application/json", "User-Agent": headers["User-Agent"]})
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
    print_jobs(fetch_analog_devices_jobs())