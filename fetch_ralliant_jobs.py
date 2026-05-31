import requests
from datetime import datetime
import time
from helper import is_old, print_jobs

def get_job_list(job_list):
    all_jobs = []
    for job in job_list:
        posted_ts = job.get("postedTs")
        posted_date = datetime.fromtimestamp(posted_ts) if posted_ts else None
        
        job_dict =  {
        "title": job.get("name"),
        "location": "; ".join(job.get("locations", [])) if job.get("locations") else None,
        "url": "https://ralliant.eightfold.ai"+job.get("positionUrl") if job.get("positionUrl") else None,
        "post_date": posted_date
        }

        all_jobs.append(job_dict)
    return all_jobs


def fetch_ralliant_jobs():
    
    url = "https://ralliant.eightfold.ai/api/pcsx/search?domain=ralliant.com&query=engineer&location=Beaverton, OR, United States&start=0&sort_by=timestamp&filter_distance=160&filter_include_remote=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://ralliant.eightfold.ai/careers?domain=ralliant.com&query=engineer&start=0&location=Beaverton%2C+OR%2C+United+States&pid=1133910682543&sort_by=timestamp&filter_distance=160&filter_include_remote=1",
        "X-Browser-Request-Time": "1777764946.341",
        "Alt-Used": "ralliant.eightfold.ai",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    jobs = r.json()

    all_jobs = get_job_list(jobs.get("data", {}).get("positions",[]))
    # Number of results returned per API page (Eightfold default for Ralliant)
    P_SIZE = 10
    # Current page number; combined with P_SIZE to calculate the next start offset
    p_num = 1
    # Total job count returned by the first request, used to drive pagination
    tot = jobs["data"]["count"] if jobs.get("data", {}).get("count") else 0

    # Paginate until the start offset exceeds the total count
    while P_SIZE * p_num < tot:
        url = f"https://ralliant.eightfold.ai/api/pcsx/search?domain=ralliant.com&query=engineer&location=Beaverton, OR, United States&start={P_SIZE * p_num}&sort_by=timestamp&filter_distance=160&filter_include_remote=1"
        time.sleep(1)
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        jobs = r.json()
        all_jobs += get_job_list(jobs.get("data", {}).get("positions",[]))      
        p_num +=1
        # Stop paging early if we've reached postings older than our threshold
        if is_old(all_jobs[-1]["post_date"]):
            return all_jobs
    
    return all_jobs


if __name__ == "__main__":
    print_jobs(fetch_ralliant_jobs())