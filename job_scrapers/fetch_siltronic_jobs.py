import requests
from datetime import datetime
from helper import print_jobs

def fetch_siltronic_jobs():
    
    sil_url = "https://recruiting.ultipro.com/SIL1005SILT/JobBoard/2208932d-db7e-4321-bf3d-9cc7f45634e3/JobBoardView/LoadSearchResults"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Length": "564",
        "Origin": "https://recruiting.ultipro.com",
        "Connection": "keep-alive",
        "Referer": "https://recruiting.ultipro.com/SIL1005SILT/JobBoard/2208932d-db7e-4321-bf3d-9cc7f45634e3/?q=&o=postedDateDesc",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    payload = {
        "opportunitySearch":
        {
            "Top":50,
            "Skip":0,
            "QueryString":"",
            "OrderBy":
            [
                {
                    "Value":"postedDateDesc",
                    "PropertyName":"PostedDate",
                    "Ascending":False
                }
            ],
            "Filters":
            [
                {
                    "t":"TermsSearchFilterDto",
                    "fieldName":4,
                    "extra":None,
                    "values":[]
                },
                {
                    "t":"TermsSearchFilterDto",
                    "fieldName":5,
                    "extra":None,
                    "values":[]
                },
                {
                    "t":"TermsSearchFilterDto",
                    "fieldName":6,
                    "extra":None,
                    "values":[]
                },
                {
                    "t":"TermsSearchFilterDto",
                    "fieldName":37,
                    "extra":None,
                    "values":[]
                }
            ]
        },
        "matchCriteria":
        {
            "PreferredJobs":[],
            "Educations":[],
            "LicenseAndCertifications":[],
            "Skills":[],
            "hasNoLicenses":False,
            "SkippedSkills":[]
        }
    }

    r= requests.post(url=sil_url,headers=headers,json=payload)
    r.raise_for_status()
    jobs = r.json()
    if jobs.get("opportunities") is None:
        return []

    job_list = []

    for job in jobs["opportunities"]:

        try:
            loc = job["Locations"][0]["Address"]
            addy=loc["Line1"]+", "+loc["City"]+", "+loc["State"]["Code"]+", "+loc["PostalCode"]
        except Exception as e:
            addy = None

        job_dict = {
            "title": job.get("Title"),
            "id": job.get("Id"),
            "post_date": datetime.fromisoformat(job.get("PostedDate")) if job.get("PostedDate") else None,
            "description": job.get("BriefDescription"),
            "url": f"https://recruiting.ultipro.com/SIL1005SILT/JobBoard/2208932d-db7e-4321-bf3d-9cc7f45634e3/OpportunityDetail?opportunityId={job.get("Id")}" if job.get("Id") is not None else None,
            "location": addy
        }

        job_list.append(job_dict)
    
    return job_list
        

if __name__ == "__main__":
    print_jobs(fetch_siltronic_jobs())
