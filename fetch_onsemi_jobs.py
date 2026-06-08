import requests
from datetime import datetime, timezone
import time
import re
from helper import is_old, print_jobs

def get_job_details(job_id):
    expand_job_url = f"https://hctz.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ById;Id=\"{job_id}\",siteNumber=CX_1001"
    expanded_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "*/*",
    "Accept-Language": "en",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://hctz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?location=Portland%2C+OR%2C+United+States&locationId=300000001620315&locationLevel=city&mode=location&radius=25&radiusUnit=MI&sortBy=POSTING_DATES_DESC",
    "Content-Type": "application/vnd.oracle.adf.resourceitem+json;charset=utf-8",
    "Ora-Irc-Language": "en",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    }
    r=requests.get(expand_job_url,headers=expanded_headers)
    r.raise_for_status()
    job_details= r.json()
    try:
        job_desc = job_details["items"][0]["ExternalDescriptionStr"]
        job_desc = re.sub(r'<[^>]+>', '', job_desc)
    except KeyError:
        job_desc = None

    try:
        job_quals = job_details["items"][0]["ExternalQualificationsStr"]
        job_quals = re.sub(r'<[^>]+>', '', job_quals)
    except KeyError:
        job_quals = None

    des = f"{job_desc}\n{job_quals}" if job_desc is not None else job_quals
    if des is None:
        return des

    des = des.replace("&nbsp;","").replace("\n\n", "\n")

    return des


def get_job_list(job_list):
    all_jobs = []
    
    # In Oracle Recruiting, jobs are sometimes nested inside items[0]['requisitionList']
    if len(job_list) == 1 and "requisitionList" in job_list[0]:
        # Oracle HCM wraps all jobs for a page inside a single items[0]['requisitionList'] list
        actual_jobs = job_list[0]["requisitionList"]
    else:
        # Fallback if structure is different
        actual_jobs = [item.get("requisitionList", [{}])[0] if "requisitionList" in item else item for item in job_list]

    # Extract standardized fields from each job record in the current page
    for job in actual_jobs:
        posted_date_str = job.get("PostedDate")
        posted_date = datetime.strptime(posted_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) if posted_date_str else None
        
        job_id = job.get("Id")
        job_deets = get_job_details(job_id)
        url = f"https://hctz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}" if job_id else None

        job_dict = {
            "title": job.get("Title"),
            "location": job.get("PrimaryLocation"),
            "url": url,
            "department": job.get("JobFamily") or job.get("JobFunction"),
            "post_date": posted_date,
            "description": job_deets,
            "id": job_id
        }

        all_jobs.append(job_dict)
    return all_jobs


def fetch_onsemi_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "*/*",
        "Accept-Language": "en",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://hctz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?location=Portland%2C+OR%2C+United+States&locationId=300000001620315&locationLevel=city&mode=location&radius=25&radiusUnit=MI",
        "Content-Type": "application/vnd.oracle.adf.resourceitem+json;charset=utf-8",
        "Ora-Irc-Language": "en",
        "Ora-Irc-Cx-UserId": "052501e5-f116-4d13-8615-d0123494febb",
        "Connection": "keep-alive",
        "Cookie": "ORA_CX_USERID=052501e5-f116-4d13-8615-d0123494febb; ORA_CX_USERID_FUNCTIONAL=052501e5-f116-4d13-8615-d0123494febb; ORA_FPC=id=823c6ae3-4782-4e6a-bc3d-83a8effd4567; ORA_CANDIDATE_NUMBER=2452564; ORA_CANDIDATE_NUMBER_FUNCTIONAL=2452564; ORA_FUSION_PREFS=v1.0~bG9jYWxlPWVufmRlZmF1bHRMYW5ndWFnZU1hcmtlcj10cnVl; ORA_FND_SESSION_US2DJ2V_F=DEFAULT_PILLAR:KLgSB9YQCswhwlkCEPkB4QTRWs2EUNrrYTYLHd+7MC/mWqio33VNa0vOJqUbl2GP:1779658630692; ak_bmsc=82F148213E01A0EE1AD60EABC87C0AC3~000000000000000000000000000000~YAAQhV7WF4MGPkCeAQAAUabrWx9/rjzdxkuh1jm48PNTP92BHsSUie6M4MROiNscM7qMdZ4yx6cl8kAZlmbx43lwMWBli1JJ9GHjgMYBFz+vjrWjSvEs7FXcanyaIegKO8sF0baDfg/3mZTSZ5G0svO/H303b/wSX5UvEd0ThA4zV16L9ub1Y2B866nA4RALe6Z4ZVLWNlW+2iJuPss4GLxwMrHt0dUzv+kMjYKvIyXn+OYyKL+7cs+5djaGPD4VBqHGk3bp0xfhqByMAlzCW16lNGBjKpE17z9cM6yu+S5/oqJr10x5IYH22osYpFGoQ1eqii/5cOGpyroDVe4YzomA2m0hIZsNc2utzH2mTRW6xBdajS2BwFj+AK1U8zHfATYnpHI8FZnVLyJtZVoVnrp35YtNxfTslw==; bm_sv=70C9EBFBF3E4A175484A96FE3E64CE39~YAAQhV7WF3YbPkCeAQAA6lfsWx+a+knqZJdCacu0OmnmxDouAJHLpMcaiWYo4F/zndHrDej4Voyq1oIekphrohCyg2AFvjA0usAX/rIBE2tw4gJ8uYcX9KR9EeoX098dTfGr40sGlpt9xtpBZrWX4lblIbvBJ6CEmWCZQnZaIWtcVUQ8suaPlyOjWR1NdBrRktO+HH50y4hq/kXIkBvMoOGQIQRhOnl4dr4x/latoC2+7l8TEUXUriEz0i1jBGaUbUwn8ZiHFzb1iica~1; CX_1001_cookieConsentEnabled=false; ORA_CX_SITE_NUMBER=CX_1001",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }

    all_jobs = []
    offset = 0
    limit = 25
    # Oracle HCM returns a 'hasMore' boolean; loop until it's False or we hit old postings
    has_more = True

    # Paginate through Oracle HCM results using limit/offset
    while has_more:
        url = f"https://hctz.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields&finder=findReqs;siteNumber=CX_1001,facetsList=LOCATIONS;WORK_LOCATIONS;WORKPLACE_TYPES;TITLES;CATEGORIES;ORGANIZATIONS;POSTING_DATES;FLEX_FIELDS,limit={limit},offset={offset},locationId=300000001620315,radius=25,radiusUnit=MI,sortBy=POSTING_DATES_DESC"
        time.sleep(0.1)
        
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        jobs_data = r.json()
        
        items = jobs_data.get("items", [])
        if not items:
            break
            
        jobs_list = get_job_list(items)
        all_jobs.extend(jobs_list)
        
        # Stop paging once we encounter a posting older than our threshold
        if jobs_list and is_old(jobs_list[-1]["post_date"]):
            break
            
        # Oracle HCM explicitly signals whether more pages exist
        has_more = jobs_data.get("hasMore", False)
        offset += limit
        
    return all_jobs

if __name__ == "__main__":
    print_jobs(fetch_onsemi_jobs())
