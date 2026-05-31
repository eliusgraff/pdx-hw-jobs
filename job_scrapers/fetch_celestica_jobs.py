import requests
import random
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from helper import is_old, print_jobs


def fetch_celestica_jobs():

    # Base URL for TSMC job postings
    base_url = "https://careers.celestica.com"
    job_query = "/search/?createNewAlert=false&q=&locationsearch=oregon"
    
    # Specific User-Agent (Windows) that works with requests for this site
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": base_url+job_query,
        "Upgrade-Insecure-Requests": "1"
    }
    
    all_jobs = []
    page = 0
    # Initialized to 1 so the loop is entered at least once; updated from first page
    total_pgs = 1 #start at 1 just to enter loop
        
    # Use a session to handle cookies automatically
    session = requests.Session()

    
    # Paginate through all result pages
    while page < total_pgs:
        
        if page > 0: time.sleep(3)
        response = session.get(base_url+job_query+"&startrow="+str(page*25), headers=headers)      
        response.raise_for_status()
        html_content = response.text
        
        if not html_content:
            #print("Failed to fetch page content after multiple attempts.")
            pass

        # Parse the raw HTML into a traversable tree
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Read the total page count from the first page's pagination element
        if page == 0:
            total_pgs = int(soup.find(class_="srHelp").text[-1])
        page += 1

        # Walk each job listing card and extract name, location, URL, and post date
        for tag in soup.find_all(class_="colTitle"):
            name = tag.find(class_="jobTitle-link")
            location = tag.find(class_="jobLocation")
            posted_tag = tag.find(class_="jobDate visible-phone")
            posted_str = posted_tag.text.strip() if posted_tag else "N/A"
            # Convert 'Posted X days ago' text into an actual datetime object
            num_days_match = re.search(r'\d+', posted_str)
            if num_days_match:
                num_days = int(num_days_match.group())
                posted_dt = datetime.now() - timedelta(days=num_days)

            job = {
                "title": name.text,
                "url": base_url + name.get("href"),
                "location": location.text.strip(),
                "post_date": posted_dt
            }

            all_jobs.append(job)
        
        # Stop paging once we reach postings that are too old
        if is_old(all_jobs[-1]['post_date']):
            return all_jobs
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_celestica_jobs())
