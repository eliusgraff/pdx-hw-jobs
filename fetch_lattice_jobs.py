import requests
from bs4 import BeautifulSoup
from helper import print_jobs
import json

def fetch_lattice_jobs():

    #lattice api is response is a bit challenging. It has one line of json with some of the interested info, then the rest you have to parse
    #from the HTML, so this works in 2 stages. The first gets the info out of the json, the second goes through the HTML tags and fills in
    #whatever else is missing

    url = "https://careers-latticesemi.icims.com/jobs/search?ss=1&searchRelation=keyword_all&searchCategory=8723&searchLocation=12781-12821-Hillsboro&mobile=false&width=1300&height=500&bga=true&needsRedirect=false&jan1offset=-480&jun1offset=-420&in_iframe=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Alt-Used": "careers-latticesemi.icims.com",
        "Connection": "keep-alive",
        "Referer": "https://careers-latticesemi.icims.com/jobs/search?ss=1&searchRelation=keyword_all&searchCategory=8723&searchLocation=12781-12821-Hillsboro&mobile=false&width=1300&height=500&bga=true&needsRedirect=false&jan1offset=-480&jun1offset=-420",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        #print(f"Error fetching jobs: {e}")
        return []
    
    #Turn json from response into list of dictionaries
    text = response.text
    start = text.find("jobImpressions")
    end = text.find(";", start) 
    job_string = text[start:end]    
    jsn = job_string.split("=", 1)[1].strip()
    jobs = json.loads(jsn)
    
    all_jobs = {}

    # Extract title, category, post_date, and id from each json entry and insert them into the all_jobs dict, indexing on idRaw
    for job in jobs:

        job_data = {
            "title": job.get("title"),
            "location": None,
            "description": None,
            "category": job.get("category"),
            "id": str(job["idRaw"]),
            "post_date": job.get("postedDate"),
            "url": None
        }

        all_jobs[job_data["id"]] = job_data


    #use beautifulsoup to go through the HTML part of the response and pull out the remaining info needed before sending to db
    soup = BeautifulSoup(text, 'html.parser')
    
    #pick out all the iCMR_JobCardItem tags for parsing
    jobs_list = soup.find_all('li', class_='iCIMS_JobCardItem')
        
    # Extract location, description, and url from each job card
    for job_card in jobs_list:
        
        locations = job_card.find(string="Job Locations").find_next().get_text().replace(" | ", ", ")[3:].strip()
        description = job_card.find(class_="col-xs-12 description").get_text().strip()
        url = job_card.find(class_="iCIMS_Anchor").get("href").strip()
        id_start = url.find("/jobs/") + len("/jobs/")
        id_end = url.find("/", id_start)
        id_raw = str(url[id_start:id_end])
        all_jobs[id_raw]["location"] = locations
        all_jobs[id_raw]["description"] = description
        all_jobs[id_raw]["url"] = url
        
    return list(all_jobs.values())

if __name__ == "__main__":
    print_jobs(fetch_lattice_jobs())