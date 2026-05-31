import requests
import json
import re
import time
from datetime import datetime
from helper import is_old, print_jobs

url = """\
https://jobs.apple.com/en-us/search?\
sort=newest&\
location=oregon-state988&\
team=field-and-solutions-engineering-SLDEV-FSE%20\
program-management-OPMFG-PRMGMT%20\
quality-engineering-OPMFG-QE%20\
procurement-OPMFG-PRC%20\
engineering-project-management-SFTWR-EPM%20\
cloud-and-infrastructure-SFTWR-CLD%20\
system-design-and-test-engineering-HRDWR-SDE%20\
reliability-engineering-HRDWR-REL%20\
engineering-project-management-HRDWR-EPM%20\
acoustic-technologies-HRDWR-ACT%20\
analog-and-digital-design-HRDWR-ADD%20\
architecture-HRDWR-ARCH%20\
battery-engineering-HRDWR-BE%20\
camera-technologies-HRDWR-CAM%20\
display-technologies-HRDWR-DISP%20\
environmental-technologies-HRDWR-ENVT%20\
health-technology-HRDWR-HT%20\
machine-learning-and-ai-HRDWR-MCHLN%20\
mechanical-engineering-HRDWR-ME%20\
process-engineering-HRDWR-PE%20\
sensor-technologies-HRDWR-SENT%20\
silicon-technologies-HRDWR-SILT%20\
wireless-hardware-HRDWR-WT%20\
apps-and-frameworks-SFTWR-AF%20\
core-operating-systems-SFTWR-COS%20\
devops-and-site-reliability-SFTWR-DSR%20\
information-systems-and-technology-SFTWR-ISTECH%20\
machine-learning-and-ai-SFTWR-MCHLN%20\
security-and-privacy-SFTWR-SEC%20\
software-quality-automation-and-tools-SFTWR-SQAT%20\
wireless-software-SFTWR-WSFT%20\
manufacturing-and-operations-engineering-OPMFG-MFGE\
"""

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def str_to_json(input_str):
    
    try:
        # Step 1: Parse the string into a Python object
        data = json.loads(input_str)
        
        # If the input was a double-encoded string (meaning it starts/ends with quotes),
        # 'data' will be a string, and we need to parse it again.
        if isinstance(data, str):
            data = json.loads(data)
            
        # Step 2: Access the job listings
        # Based on the sample, jobs are in loaderData -> search -> searchResults
        # or just search -> searchResults if the string was just that part
        search_data = data.get("search") or data.get("loaderData", {}).get("search", {})
        jobs = search_data.get("searchResults", [])       
            
        return data
    except json.JSONDecodeError as e:
        #print(f"Error decoding JSON: {e}")
        return None


def fetch_apple_jobs():
    """Fetches all job listings by iterating through paginated results."""
    all_jobs = []
    page = 1
    total_records = 0
    
    # Extract the base URL without query parameters for cleaner manipulation
    base_search_url = url.split("?")[0]
    query_params = url.split("?")[1].replace("\n", "").replace(" ", "")
    
    # Keep fetching pages until all jobs are collected or an old posting is found
    while True:
        # Construct the URL for the current page
        current_url = f"{base_search_url}?{query_params}&page={page}"
        #print(f"Fetching page {page}...")
        
        # Download HTML for the current page
        html = get_apple_html(current_url)
        json_str = extract_json_string(html)
        
        if not json_str:
            break
            
        data = json.loads(json_str)
        if isinstance(data, str):
            data = json.loads(data)
            
        search_data = data.get("search") or data.get("loaderData", {}).get("search", {})
        jobs = search_data.get("searchResults", [])
        
        # Read the total record count from the first page to know when to stop
        if page == 1:
            total_records = search_data.get("totalRecords", 0)
            #print(f"Total jobs to fetch: {total_records}")
            
        if not jobs:
            break
            
        # Normalize each job record into our standard dictionary format
        for job in jobs:
            job_info = {
                "id": job.get("id"),
                "title": job.get("postingTitle"),
                "location": job.get("locations")[0].get("name") if job.get("locations") else "Unknown",
                "post_date": datetime.strptime(job.get("postingDate"), "%b %d, %Y"),
                "url": f"https://jobs.apple.com/en-us/details/{job.get('id')}"
            }
            all_jobs.append(job_info)
        
        # Stop once we've collected everything the API has to offer
        if len(all_jobs) >= total_records or not jobs:
            break

        # Check the age of the last job on this page before requesting the next one
        last_job = datetime.strptime(jobs[-1].get("postingDate"), "%b %d, %Y")
        if is_old(last_job):
            #print("Jobs are too old now, no need to store them. Stopping")
            break

        page += 1
        time.sleep(1) # Be respectful to the API
        
    return all_jobs

def get_apple_html(target_url):
    try:
        response = requests.get(target_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return ""


def extract_json_string(html):
    # This regex captures the string inside JSON.parse("...")
    # It handles escaped quotes inside the JS string literal
    match = re.search(r'JSON\.parse\("((?:[^"\\]|\\.)*)"\);', html, re.DOTALL)
    if not match:
        return None

    raw_literal = match.group(1)
    try:
        # The most robust way to unescape a JS string literal is to treat it
        # as a JSON string literal. Wrap it in quotes and use json.loads.
        # This handles \" and other escapes correctly without breaking nested JSON.
        unescaped = json.loads('"' + raw_literal + '"')
        return unescaped
    except json.JSONDecodeError as e:
        print(f"Extraction error: {e}")
        # Fallback to simple replace if necessary
        return raw_literal.replace('\\"', '"').replace('\\/', '/')


if __name__ == "__main__":
    print_jobs(fetch_apple_jobs())