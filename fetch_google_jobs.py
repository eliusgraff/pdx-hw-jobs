import requests
from helper import print_jobs

def extract_jobs(html_content):
    
    # Delimiter used to locate individual job entries within the raw HTML
    look_str = "</h3></div></div><div class"
    loc_start_str= "| <span class="
    location_end_str = "</span></span></p></div><div"
    backup_loc_end_str = "<div"
    job_list = list()

    start = html_content.find(look_str)
    pointer = start

    # Walk through every job entry found in the HTML until none remain
    while start > -1:

        #Get the whole chunk of HTML between the </h3></div></div><div class delimiters
        tag_end = html_content.find(look_str, start+1)
        start=html_content.rfind(">",0, start) + 1
        job_chunk = html_content[start:tag_end]

        #Get the name from the chunk
        pointer = html_content.find("</h3",start)
        job_name = html_content[start:pointer]
        href_start = html_content.find("href=",pointer)
        
        #get job location details

        # Locate the location span within the current job chunk
        location_start_index = html_content.find(loc_start_str, pointer)
        location_end_index = html_content.find(location_end_str, location_start_index)
        bu_loc_end_index = html_content.find(backup_loc_end_str, location_start_index)

        loc_str = ""
        if location_end_index != -1 and bu_loc_end_index != -1:
            location_end_index = min(location_end_index, bu_loc_end_index)
            loc_str = html_content[location_start_index+len(loc_start_str):location_end_index+3] #+3 needed to include some charaters to find end of html tags
        else:
            location_end_index = max(location_end_index, bu_loc_end_index)
            loc_str = html_content[location_start_index+len(loc_start_str):location_end_index] + "</s" # appended string is needed for parsing in the next section
        
        job_location=extract_location_details(loc_str) if len(loc_str) < 500 else "*Error Finding Location, See Google Website Directly*"

        #Find each of the <li> tags and add those together as the description/experience
        line_delim = "<li>"
        delim_len = len(line_delim)
        line_start = html_content.find(line_delim,pointer)+delim_len
        job_des = ""
        while line_start < href_start and line_start > delim_len:
            pointer = html_content.find("<",line_start)
            job_des += html_content[line_start:pointer]+"\n"
            line_start = html_content.find(line_delim,pointer)+delim_len
        
        #Find the href= extract the job id from it and add "https://www.google.com/about/careers/applications/" to the beginning of it to get he url
        href_start += len("href=\"")
        pointer = html_content.find("-",href_start)
        job_id = html_content[href_start:pointer]
        pointer = html_content.find("\"",pointer)
        href = html_content[href_start:pointer]
        job_url = "https://www.google.com/about/careers/applications/" + href

        start = html_content.find(look_str, pointer)
        pointer = start

        job_tag = {
            "title": job_name,
            "location": job_location,
            "url": job_url,
            "description": job_des
        }

        '''for k,v in job_tag.items():
            print(f"{k}: {v}")
        print("-" *20)'''

        job_list.append(job_tag)

    return job_list


def extract_location_details(html_str):
    
    #print(html_str)
    #input("loc string input")
    i=html_str.find("\">")+2 #+2 needed to account for the length of '\>'
    locations = []

    while i > -1:

        start = html_str.find("\">", i)
        finish = html_str.find("</s", start)
        if finish == -1:
            finish = html_str.find("<h4", start)
        #print(html_str[start:finish])
        #print(f"i: {i} s: {start} f: {finish}")
        locations.append(html_str[start+2:finish]) #+2 needed to account for the length of '\>'
        i = html_str.find("<", finish)

    #last location will have not have location data in it, so just drop it before returning
    locations = "".join(locations[:-1])
    #print(locations)
    return locations


def fetch_google_jobs():
    """Fetches the webpage and extracts h3 details."""
    url = "https://www.google.com/about/careers/applications/jobs/results?location=Portland%2C%20OR%2C%20USA&sort_by=date"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    return extract_jobs(response.text)

if __name__ == "__main__":
    print_jobs(fetch_google_jobs())
