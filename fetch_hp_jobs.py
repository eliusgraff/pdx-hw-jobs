import requests
from datetime import datetime
import time
from helper import is_old, print_jobs


def get_job_list(job_list):
    all_jobs = []
    for job in job_list:
        posted_date = datetime.fromtimestamp(job["postedTs"]) if job.get("postedTs") is not None else None
        
        job_dict =  {
        "title": job.get("name"),
        "location": "; ".join(job.get("locations", [])) if job.get("locations") else None,
        "url": "https://apply.hp.com"+job.get("positionUrl") if job.get("positionUrl") else None,
        "department": job.get("department"),
        "post_date": posted_date,
        "id" : str(job["id"]) if job.get("id") is not None else None
        }

        all_jobs.append(job_dict)
    return all_jobs


def fetch_hp_jobs():
    
    url = "https://apply.hp.com/api/pcsx/search?domain=hp.com&query=&location=Vancouver, WA, United States&start=0&="

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://apply.hp.com/careers?start=0&location=Vancouver%2C++WA%2C++United+States&pid=27375457&sort_by=timestamp&filter_distance=80&filter_include_remote=1",
        "Alt-Used": "apply.hp.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    jobs = r.json()

    all_jobs = get_job_list(jobs.get("data", {}).get("positions",[]))
    # Number of results returned per API page (HP eightfold API default)
    P_SIZE = 10
    # Current page number; combined with P_SIZE to calculate the start offset
    p_num = 1
    # Total job count returned by the first request, used to drive pagination
    tot = jobs["data"]["count"] if jobs.get("data", {}).get("count") else 0

    # Paginate until start offset exceeds total count
    while P_SIZE * p_num < tot:
        url = f"https://apply.hp.com/api/pcsx/search?domain=hp.com&query=&location=Vancouver, WA, United States&start={p_num*P_SIZE}&sort_by=timestamp&filter_distance=80&filter_include_remote=1"
        time.sleep(1)
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        jobs = r.json()
        all_jobs += get_job_list(jobs.get("data", {}).get("positions",[]))
        p_num +=1

        #No need to keep paging if all the jobs are going to be from too long ago
        if is_old(all_jobs[-1]["post_date"]):
            break

    return all_jobs
    

if __name__ == "__main__":
    print_jobs(fetch_hp_jobs())