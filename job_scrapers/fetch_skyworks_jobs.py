import requests
from datetime import datetime
from helper import is_old, print_jobs


def fetch_skyworks_jobs():
    
    url = "https://careers.skyworksinc.com/services/recruiting/v1/jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://careers.skyworksinc.com/search/?q=&locationsearch=&searchResultView=LIST&pageNumber=0&facetFilters=%7B%22req_country%22%3A%5B%22United+States%22%5D%2C%22jobLocationState%22%3A%5B%22Oregon%22%5D%2C%22sfstd_jobLocation_obj%22%3A%5B%22Hillsboro%22%5D%7D&sortBy=&markerViewed=&carouselIndex=",
        "Content-Type": "application/json",
        "Origin": "https://careers.skyworksinc.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

    payload = {
    "locale": "en_US",
    "pageNumber": 0,
    "sortBy": "date",
    "keywords": "",
    "location": "",
    "facetFilters": {
        "req_country": ["United States"],
        "jobLocationState": ["Oregon"],
        "sfstd_jobLocation_obj": ["Hillsboro"]
    },
    "brand": "",
    "skills": [],
    "categoryId": 0,
    "alertId": "",
    "rcmCandidateId": ""
    }

    # Number of results returned per API page (Skyworks default)
    PAGE_LENGTH = 10

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    tot_jobs = data.get('totalJobs', 0)
    page_num = 0
    all_jobs = []

    # Paginate until start offset exceeds total job count
    while PAGE_LENGTH*page_num < tot_jobs:
        
        # Skip re-fetching the first page since it was already done above the loop
        if page_num > 0:
            payload["pageNumber"] = page_num
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

        # Walk each job entry and normalize it into our standard format
        for job in data.get("jobSearchResult",[]):
            
            job_info = job.get("response")
            if job_info is None:
                continue

            job_tag = {
                "title":job_info.get("unifiedStandardTitle", job_info.get("unifiedUrlTitle", job_info.get("urlTitle", "No Name Found..."))),
                "id": job_info.get("id", "No Id Found..."),
                "department": ",".join(job_info.get("jobFunction_obj", [])),
                "url": "https://careers.skyworksinc.com/job/"+ job_info.get("urlTitle") + job_info.get("supportedLocales")[0] if job_info.get("urlTitle") and job_info.get("supportedLocales") else None,
                "post_date": datetime.strptime(job_info.get("unifiedStandardStart"), "%m/%d/%y") if job_info.get("unifiedStandardStart") else None,
                "location": ";".join(loc.strip() for loc in job_info.get("jobLocationShort",[]))
            }

            all_jobs.append(job_tag)

        # Stop paging once we encounter postings older than our threshold
        if is_old(all_jobs[-1]["post_date"]):
            return all_jobs

        page_num += 1


if __name__ == '__main__':
    print_jobs(fetch_skyworks_jobs())

    