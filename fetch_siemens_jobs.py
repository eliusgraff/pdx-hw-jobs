import requests
from bs4 import BeautifulSoup
from helper import print_jobs

def fetch_siemens_jobs():
    base_url = "https://jobs.siemens.com"
    search_url = (
        f"{base_url}/en_US/externaljobs/SearchJobs/"
        "?42386=[812209]&42387=[814830]&42388=[15071802]&42389=[102117]"
        "&42386_format=17546&42387_format=17547&42388_format=17879&42389_format=17549"
        "&listFilterMode=1&folderSort=postedDate&folderSortDirection=ASC"
        "&folderRecordsPerPage=25&="
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    r = requests.get(search_url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    # Each job result is an <article> with class 'article--result'
    articles = soup.find_all("article", class_="article--result")

    all_jobs = []

    # Extract title, URL, location, job ID, and department from each result card
    for article in articles:
        # Title and URL
        title_tag = article.find("h3", class_="article__header__text__title")
        link_tag = title_tag.find("a", class_="link") if title_tag else None
        title = link_tag.get_text(strip=True) if link_tag else None
        url = link_tag["href"] if link_tag and link_tag.has_attr("href") else None

        # Location
        location_tag = article.find("span", class_="list-item-location")
        location = location_tag.get_text(strip=True) if location_tag else None

        # Job ID
        job_id_tag = article.find("span", class_="list-item-jobId")
        job_id = job_id_tag.get_text(strip=True).replace("Job ID: ", "") if job_id_tag else None

        # Department / field of work (third span in subtitle, after separators)
        subtitle_tag = article.find("div", class_="article__header__text__subtitle")
        department = ""
        if subtitle_tag:
            spans = [
                s for s in subtitle_tag.find_all("span")
                if "separator" not in s.get("class", [])
                and "list-item-location" not in s.get("class", [])
                and "list-item-jobId" not in s.get("class", [])
            ]
            if spans:
                department = spans[-1].get_text(strip=True)

        job_dict = {
            "title": title,
            "id": job_id,
            "location": location,
            "department": department,
            "url": url,
        }


        all_jobs.append(job_dict)

    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_siemens_jobs())