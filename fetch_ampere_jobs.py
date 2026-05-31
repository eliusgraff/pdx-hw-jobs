import requests
from bs4 import BeautifulSoup
import time
from helper import print_jobs


def fetch_ampere_jobs():

    # Base URL for Ampere job postings
    base_url = "https://careers.amperecomputing.com"
    job_query = "/search/jobs?q=&location=Oregon"
    
    # Specific User-Agent (Windows) that works with requests for this site
    my_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://careers.amperecomputing.com/search/jobs/in?location=Oregon&page=2",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    all_jobs = []
    page = 1
    # Initialized to 2 so the loop is entered at least once; updated from first page
    total_pgs = 2 #start at 1 just to enter loop
        
    # Use a session to handle cookies automatically
    session = requests.Session()

    # Paginate through all result pages
    while page < total_pgs:
        
        #Wait so not to spam endpoint
        if page > 0: time.sleep(3)

        #Make request to get job webpage data
        response = session.get(base_url+job_query+f"&page={page}", headers=my_headers)      
        response.raise_for_status()
        html_content = response.text
        if not html_content:
            #print("Failed to fetch page content")
            continue

        # Parse the raw HTML into a traversable tree
        soup = BeautifulSoup(html_content, 'html.parser')
        
        #Get total number of pages to parse
        if page == 0:
            total_pgs = int(soup.find(class_="small-text padded-v-medium").text.strip())
        page += 1

        #Go though each of the tags found which contain jobs and parse them
        for tag in soup.find_all(class_="jobs-section__item padded-v-small"):

            #pick out tag with the job title in it
            name = tag.find(class_="heading-6 space-none")

            #Search through all the tags until the location one is found
            for large_tag in tag.find_all(class_="large-3 columns"):
                if "Location" in large_tag.text:
                    location = large_tag
                    break
            #Process location tag data
            location = location.text.strip()
            location = "".join(location.replace("Location:", "").split())
            location = location.replace(",", ", ").replace("UnitedStates", "United States")

            #Process name tag data to get the url to the job posting out of it
            name_tag_str = str(name)
            # Pull the job URL out of the anchor tag's href attribute
            start = name_tag_str.find("href=")
            end = name_tag_str.find("\">", start)
            url = name_tag_str[start+len("href=")+1:end]
            
            #Sometimes they add newlines into job title string, this removes that
            title_text = name.text.strip()
            delim = title_text.find("\n")
            title = title_text if delim == -1 else title_text[:delim]

            #Turn all job data into a dictionary and save it
            job = {
                "title": title,
                "url": url,
                "location": location
            }
            all_jobs.append(job)
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_ampere_jobs())