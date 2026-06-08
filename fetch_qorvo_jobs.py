import requests
from bs4 import BeautifulSoup
from helper import print_jobs
from datetime import datetime

def fetch_qorvo_jobs():
    qorvo_host = "https://careers.qorvo.com"
    url = f"{qorvo_host}/search/?createNewAlert=false&q=&optionsFacetsDD_city=Hillsboro&optionsFacetsDD_country=&optionsFacetsDD_department=&optionsFacetsDD_customfield1=&optionsFacetsDD_customfield2=&optionsFacetsDD_customfield4="
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": f"{qorvo_host}/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    wp_html = r.text

    # Parse the HTML job listing page
    soup = BeautifulSoup(wp_html, "html.parser")
    # Each job listing is contained in a 'jobdetail-phone' div
    job_list = soup.find_all("div", class_="jobdetail-phone visible-phone")
    all_jobs =[]

    # Extract title, location, and URL from each job card
    for job_tag in job_list:
        
        # Skip any empty tags that may appear in the HTML
        if len(str(job_tag).strip()) == 0:
            continue
        title_tag = job_tag.find("a", class_="jobTitle-link")
        title = title_tag.get_text(strip=True) if title_tag else None

        location_tag = job_tag.find("span", class_="jobLocation")
        location = location_tag.get_text(strip=True) if location_tag else ""

        job_dict = {
            "title": title,
            "location": location,
            "url": qorvo_host+title_tag["href"] if title_tag and title_tag.has_attr("href") else None,
            "id": title_tag["href"].split("/")[-2] if title_tag and title_tag.has_attr("href") else None,
            "post_date": datetime.now()
        }

        all_jobs.append(job_dict)
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_qorvo_jobs())