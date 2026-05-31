import requests
from bs4 import BeautifulSoup
from helper import print_jobs



def fetch_lattice_jobs():
    url = "https://careers-latticesemi.icims.com/jobs/search?ss=1&searchRelation=keyword_all&searchCategory=8723&searchLocation=12781-12821-Hillsboro&in_iframe=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    
    #print(f"Fetching jobs for Lattice from {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        #print(f"Error fetching jobs: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    #pick out all the iCMR_JobCardItem tags for parsing
    jobs_list = soup.find_all('li', class_='iCIMS_JobCardItem')
    
    all_jobs = []
    
    # Extract title, location, description, and ID from each job card
    for job_card in jobs_list:
        locations = job_card.find(string="Job Locations").find_next().get_text().replace(" | ", ", ")[3:].strip()
        title = job_card.find(string="Title").find_next().get_text().strip()
        description = job_card.find(class_="col-xs-12 description").get_text().strip()
        category = job_card.find(class_="iCIMS_JobHeaderData").get_text().strip()
        id = job_card.find(string="ID").find_next().get_text().strip()
        job_data = {
            "title": title,
            "location": locations,
            "description": description,
            "category": category,
            "id": id
        }
        all_jobs.append(job_data)
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_lattice_jobs())