import requests
from datetime import datetime
from helper import is_old, print_jobs


def fetch_compunet_jobs():
    url = "https://job-boards.greenhouse.io/compunetinc?offices[]=4006624008&_data=routes/$url_token"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://job-boards.greenhouse.io/compunetinc",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    json_data = response.json()

    jobs = json_data.get("jobPosts", {}).get("data",{})
    all_jobs = []
    page_num = 0

    # Total number of pages to paginate through
    tot_pages = json_data.get("jobPosts", {}).get("total_pages",0)

    # Paginate until all pages have been processed
    while page_num < tot_pages:
        
        #already done for the first pass, so only need to get new page on subsequent passes
        if page_num > 0:
            url = f"https://job-boards.greenhouse.io/compunetinc?offices[]=4006624008&page={page_num}&_data=routes/$url_token"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            json_data = response.json()

        for job in jobs:

            #For some reason the site responds with all instances of jobs that have a location in portland. 
            # this will just filter those out that are not actually in portland
            if job.get("location","").find(", OR") == -1:
                continue

            job_tag = {
                "title": job.get("title"),
                "id": str(job.get("id")),
                "post_date": datetime.fromisoformat(job.get("updated_at")).replace(tzinfo=None) if job.get("updated_at") else None,
                "url": job.get("absolute_url"),
                "location": job.get("location"),
                "department": job["department"].get("name") if job.get("department") else None
            }

            all_jobs.append(job_tag)

        # Stop paging once we reach postings that are too old
        if is_old(all_jobs[-1]["post_date"]):
            return all_jobs
        page_num += 1

    jobs = json_data.get("jobPosts", {}).get("data",{})

    return all_jobs

if __name__ == '__main__':
    print_jobs(fetch_compunet_jobs())