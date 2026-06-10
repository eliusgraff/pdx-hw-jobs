import requests
from datetime import datetime
from helper import print_jobs
from bs4 import BeautifulSoup as beso
import time

#Returns number of results found from webpage
def get_result_num(wp_soup):
    
    #At the top of each webpage in the section__title--3 section it should say "XY Results". Just return XY from that string
    tags = wp_soup.find_all('h5', class_='section__title--3')
    if not tags: return 0
    return int(tags[0].text.strip().split(" ")[0]) if tags[0].text.strip().split(" ")[0].isdigit() else 0


def fetch_koch_jobs():
    base_url = "https://koch.avature.net/en_US/careers/SearchJobs"
    payload = {
        "730": "",
        "731": "",
        "732": "",
    }
    url = "https://koch.avature.net/en_US/careers/SearchJobs/?954=[337265]&955=[329059]&954_format=6171&955_format=6307&listFilterMode=1&jobRecordsPerPage=6&="
    
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://koch.avature.net/en_US/careers/SearchJobs/?954=%5B331475%5D&954_format=6171&955=%5B329059%5D&955_format=6307&listFilterMode=1&jobRecordsPerPage=6&",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    
    session.headers.update(headers)
    
    all_jobs = []
    
    try:
        response = session.get(url)
        response.raise_for_status()
        wp_text = response.text
        print(wp_text)
        wp_soup = beso(wp_text, "html.parser")
        
    except requests.exceptions.RequestException as e:
        exit(e)


    articles = wp_soup.find_all('article', class_='article--result')
    for article in articles:
        a_tag = article.find('a', href=lambda x: x and '/JobDetail/' in x)
        if not a_tag:
            continue
            
        title = a_tag.text.strip()
        full_url = a_tag.get('href')
        job_id = full_url.rstrip('/').split('/')[-1]
        
        location = "Unknown"
        labels = article.find_all('div', class_='article__content__field__label')
        values = article.find_all('div', class_='article__content__field__value')
        for label, value in zip(labels, values):
            if 'Location:' in label.text:
                location = value.text.strip()
                break
                
        posted_date = datetime.now()

        job_info = {
            "id": job_id,
            "title": title,
            "location": location,
            "post_date": posted_date,
            "url": full_url
        }
        all_jobs.append(job_info)
            
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_koch_jobs())
