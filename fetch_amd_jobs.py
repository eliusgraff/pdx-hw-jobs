import requests
import json
from datetime import datetime
from helper import is_old, print_jobs
import time

def fetch_amd_jobs():
    url = "https://careers.amd.com/api/jobs?page=1&location=portland&stretch=50&stretchUnit=MILES&country=United States&sortBy=posted_date&descending=true&internal=false"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": "https://careers.amd.com/careers-home/jobs?page=1&location=portland&stretch=50&stretchUnit=MILES&country=United%20States",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    all_jobs = []
    # Starts at 0; set from first API response. Also acts as the loop sentinel until initialized
    display_limit = 0
    # Initialized to 1 so the while condition is True on the first pass
    total_found = 1 #starts at 1 to make sure the loop is entered at least once
    pg = 1

    # Paginate until we've retrieved all available jobs
    while (pg * display_limit) < total_found:

        #issue get request to api for json of job details
        r = requests.get(f"https://careers.amd.com/api/jobs?page={pg}&location=Oregon&stretch=50&stretchUnit=MILES&country=United States&sortBy=posted_date&descending=true&internal=false", headers=headers)
        r.raise_for_status()
        wp_content = json.loads(r.text)

        #set paging up on first pass and increment number for each pass. If this is not the first pass, wait 3 sec to be nice to the endpoint
        if display_limit == 0:
            display_limit = wp_content['filter']['displayLimit']
            total_found = wp_content['totalCount']
        else:
            time.sleep(1)
        pg += 1

        #Go through each of the job tags and extract the details of the job
        for tag in wp_content['jobs']:
            
            each = tag['data']
            job_deets = {
                'title': each.get('title'),
                'id': each.get('req_id'),
                'description': each.get('responsibilities'),
                'post_date': each.get('posted_date'),
                'url': each.get('apply_url'),
                'location': each.get('location_name')
            }
            
            all_jobs.append(job_deets)

        #Some jobs get kept up too long. Anything older than 6 months gets dropped
        try:
            last_date = datetime.fromisoformat(all_jobs[-1]['post_date']).replace(tzinfo=None)
            if is_old(last_date):
                return all_jobs
        except IndexError:
            return all_jobs
        except KeyError:
            continue

    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_amd_jobs())
    