import requests
from bs4 import BeautifulSoup
from helper import print_jobs

def fetch_nfi_jobs():
    url = "https://careers.nearfieldinstruments.com/jobs?jobs-f1082b85[country][]=US"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
        }
    all_jobs = []
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    wp_content = r.text
    
    if not wp_content:
        return

    # Parse the HTML response into a traversable tree
    soup = BeautifulSoup(wp_content, 'html.parser')
    # Target the desktop job listing container by its data-testid attribute
    filtered_tags = soup.find("div", attrs={"data-testid":"offer-list-cards-desktop-display"})

    for job in filtered_tags.find_all(href=True):
        if job.text == "View job":
            continue

        job_details = {
            "title":job.text,
            "url": "https://careers.nearfieldinstruments.com"+job['href'] if job.get('href') else None
        }
        all_jobs.append(job_details)

    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_nfi_jobs())