import requests
from datetime import datetime
from helper import is_old, print_jobs
import time


def fetch_cisco_jobs():
    base_url = "https://careers.cisco.com/widgets"
    
    # This payload is derived from the user's provided JSON
    payload = {
        "sortBy":"Most recent",
        "subsearch":"",
        "from":0,
        "jobs":True,
        "counts":True,
        "all_fields":[
            "category",
            "raasJobRequisitionType",
            "country",
            "state",
            "city",
            "type",
            "RemoteType"
            ],
        "pageName":"product-and-engineering",
        "pageType":"category",
        "size":10,
        "clearAll":False,
        "jdsource":"facets",
        "isSliderEnable":False,
        "pageId":"page490-prod",
        "siteType":"external",
        "keywords":"",
        "global":True,
        "selected_fields":{
            "category":["Product and Engineering","Project and Program Management"],
                "country":["United States of America"],
                "state":["Oregon"],
                "raasJobRequisitionType":["Professional"],
                "type":["Full time"],
                "city":["Portland"]
            },
        "sort":{
            "order":"desc",
            "field":"postedDate"
        },
        "lang":"en_global",
        "deviceType":"desktop",
        "country":"global",
        "refNum":"CISCISGLOBAL",
        "ddoKey":"refineSearch"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://careers.cisco.com/global/en/c/product-and-engineering-jobs"
    }
    
    all_jobs = []
    start = 0
    # Initialized to 1 so the while loop is entered on the first pass
    total = 1 # Initial value to start the loop
    # Number of results fetched per API call
    page_size = 10 # In case more than 10 jobs pop up, page through 10 at a time
    
    #print(f"Fetching jobs for Cisco from {base_url}")
    
    # Paginate until all jobs have been retrieved
    while start < total:
        
        payload["from"] = start
        try:
            response = requests.post(base_url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            #print(f"Error fetching jobs: {e}")
            break

        data = response.json()
        
        '''with open("csco.txt",'w') as file:
            json.dump(data, file, indent=2)'''
        
        
        # Update total only on the first request
        if start == 0:
            total = data["refineSearch"]["totalHits"]

        jobs_list = data["refineSearch"]["data"]["jobs"]

        # Normalize each job record into our standard dictionary format
        for job_tag in jobs_list:
            
            job_info = {
                "title": job_tag.get("title"),
                "location": ", ".join(job_tag.get("multi_location", job_tag.get("cityState"))) if job_tag.get("multi_location", job_tag.get("cityState")) else None,
                "post_date": datetime.strptime(job_tag.get("postedDate"), "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None) if job_tag.get("postedDate") else None,
                "url":job_tag.get("applyUrl"),
                "department":", ".join(job_tag.get("multi_category")) if job_tag.get("multi_category") else None,
                "description":job_tag.get("descriptionTeaser")
            }

            all_jobs.append(job_info)

        #Check to see if theere are still recent jobs before requesting older ones
        last_date = job_tag.get("post_date",None)
        if last_date is not None:
            # Parse and remove timezone awareness
            dt_object = datetime.strptime(last_date, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            
            # If jobs are over 6mos old, then we can stop looking at them, they are too old
            if is_old(dt_object):
                #print("Jobs too old - stopping!")
                break

        start += page_size
        # Sleep to avoid spamming api
        time.sleep(1)
    return all_jobs
    
if __name__ == "__main__":
    print_jobs(fetch_cisco_jobs())
