import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from helper import is_old, print_jobs

class Scrape_Exception (Exception):
    pass


def fetch_tsmc_jobs():
    """
    Scrapes job postings for TSMC in Camas, WA using a filtered URL.
    Uses the requests library and manual string manipulation (no urllib.parse).
    """
    # Base URL for TSMC job postings
    site_root = "https://careers.tsmc.com"
    base_url = f"{site_root}/en_US/careers/SearchJobs/"
    
    # Specific User-Agent (Windows) that works with requests for this site
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://careers.tsmc.com/en_US/careers/SearchJobs",
        "Upgrade-Insecure-Requests": "1"
    }
    
    all_jobs = []
    # Tracks how many jobs have been fetched so far; used as the page offset
    offset = 0
    # Populated from the first page; None signals we haven't read it yet
    total_found = None
        
    # Use a session to handle cookies automatically
    session = requests.Session()
    
    while True:
        # Construct parameters manually
        params = {
            "1277": "13222",
            "1277_format": "1380",
            "listFilterMode": "1",
            "jobRecordsPerPage": "10",
            "jobOffset": str(offset),
            "jobSort":"postedDate",
            "jobSortDirection":"DESC"
        }
        
        # Retry up to 3 times per page in case of transient errors or Cloudflare blocks
        max_retries = 3
        html_content = ""
        
        for attempt in range(max_retries):
            try:
                response = session.get(base_url, headers=headers, params=params)
                
                # TSMC uses Cloudflare; a 403 with 'Just a moment...' means we've been flagged
                if response.status_code == 403:
                    
                    if "Just a moment..." in response.text:
                        print(f"Cloudflare block detected on attempt {attempt + 1}. Retrying...")
                        time.sleep(0.5)
                        continue
                    
                    else:
                        print(f"Error 403: Forbidden")
                        break
                
                response.raise_for_status()
                html_content = response.text
                break
                
            except requests.exceptions.RequestException as e:
                time.sleep(0.5)
        
        if not html_content:
            break
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find total count
        if total_found is None:
            legend = soup.select_one(".list-controls__text__legend")
            
            if legend:
                text = " ".join(legend.stripped_strings)
                
                if "of" in text:
                    parts = text.split("of")
                    
                    try:
                        total_found = int(parts[1].strip().split()[0])
                    
                    except (ValueError, IndexError):
                        total_found = 0
                
                else:
                    total_found = 0
            
            else:
                
                if "No results" in html_content or "0 results" in html_content:
                    total_found = 0
                
                else:
                    
                    if soup.select("article.article--result"):
                        total_found = float('inf')
                    
                    else:
                        total_found = 0
        
        if total_found == 0:
            print("No jobs found.")
            break
            
        job_articles = soup.select("article.article--result")
        if not job_articles:
            break
            
        # Extract job info from each <article> result card on the current page
        for article in job_articles:
            title_link = article.select_one("h3.article__header__text__title a.link")
            if not title_link:
                continue
                
            title = title_link.get_text(strip=True)
            relative_url = title_link.get("href", "")
            
            # Manual URL joining
            if relative_url.startswith("http"):
                full_url = relative_url
            elif relative_url.startswith("/"):
                full_url = site_root + relative_url
            else:
                full_url = base_url + relative_url
            
            # Manual Job ID extraction from query string
            # e.g., ...?jobId=19779&source=...
            job_id = "N/A"
            # Extract the job ID from the URL query string
            if "jobId=" in full_url:
                tmp = full_url.split("jobId=")[1]
                job_id = tmp.split("&")[0]
            
            location_el = article.select_one("span.list-item-location")
            location = location_el.get_text(strip=True) if location_el else "N/A"
            
            # Fetch job details page to get posted date and description
            posted_str = "N/A"
            description = "N/A"
            
            try:
                # Follow-up request to the job detail page to get the posted date and description
                detail_resp = session.get(full_url, headers=headers)
                if detail_resp.status_code == 403 and "Just a moment..." in detail_resp.text:
                    raise Scrape_Exception
                    
                detail_resp.raise_for_status()
                detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                
                # Extract date and check if the job is too old for us
                date_div = detail_soup.select_one("div.tf_date div.article__content__view__field__value")
                if date_div:
                    posted_str = date_div.get_text(strip=True)
                    try:
                        parsed_date = datetime.strptime(posted_str, "%b %d, %Y")
                        if is_old(parsed_date):
                            return all_jobs
                    except ValueError:
                        pass
                
                # Extract description
                details_articles = detail_soup.find_all("article", class_="article--details")
                for a in details_articles:
                    if "regular-fields-label--title" in a.get("class", []):
                        val_div = a.select_one("div.article__content__view__field__value")
                        if val_div:
                            description = val_div.get_text(separator="\n", strip=True)
                            break
            except Scrape_Exception:
                #print(f"Suspect Cloudflare issue during getting additional info for {title} skipping the rest of this one")
                pass
            except requests.exceptions.RequestException as e:
                #print(f"Problem getting additional info for {title} skipping the rest of this one")
                pass

            # Strip the boilerplate header text that precedes the actual job description
            filter_string = "with a commitment to excellence and innovation."
            desc_start = description.find(filter_string) + len(filter_string)
            desc_end = description.find("Eligibility:",desc_start)
            description = description[desc_start:desc_end]

            job_info = {
                "id": job_id,
                "title": title,
                "location": location,
                "post_date": parsed_date,
                "url": full_url,
                "description": description
            }
            all_jobs.append(job_info)
         
        # Advance the offset by however many jobs were on this page
        offset += len(job_articles)
        if offset >= total_found:
            break
                        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_tsmc_jobs())