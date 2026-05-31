import mysql.connector
import os
import datetime
from concurrent.futures import ThreadPoolExecutor
import time
import traceback

from fetch_amat_jobs import fetch_amat_jobs
from fetch_amd_jobs import fetch_amd_jobs
from fetch_ampere_jobs import fetch_ampere_jobs
from fetch_analog_devices_jobs import fetch_analog_devices_jobs
from fetch_apple_jobs import fetch_apple_jobs
from fetch_autodesk_jobs import fetch_autodesk_jobs
from fetch_celestica_jobs import fetch_celestica_jobs
from fetch_cisco_jobs import fetch_cisco_jobs
from fetch_compunet_jobs import fetch_compunet_jobs
from fetch_google_jobs import fetch_google_jobs
from fetch_hp_jobs import fetch_hp_jobs
from fetch_intel_jobs import fetch_intel_jobs
from fetch_kla_jobs import fetch_kla_jobs
from fetch_lam_jobs import fetch_lam_jobs
from fetch_lattice_jobs import fetch_lattice_jobs
from fetch_marvell_jobs import fetch_marvell_jobs
from fetch_microchip_jobs import fetch_microchip_jobs
from fetch_microsoft_jobs import fetch_microsoft_jobs
from fetch_nearfield_jobs import fetch_nfi_jobs
from fetch_nvidia_jobs import fetch_nvidia_jobs
from fetch_onsemi_jobs import fetch_onsemi_jobs
from fetch_qorvo_jobs import fetch_qorvo_jobs
from fetch_qualcomm_jobs import fetch_qualcomm_jobs
from fetch_ralliant_jobs import fetch_ralliant_jobs
from fetch_siemens_jobs import fetch_siemens_jobs
from fetch_siltronic_jobs import fetch_siltronic_jobs
from fetch_skyworks_jobs import fetch_skyworks_jobs
from fetch_tsmc_jobs import fetch_tsmc_jobs
from fetch_vgems_jobs import fetch_vgems_jobs

#This function only parses lines if query matches the description. It puts the matched lines into a dictionary where the 
#variable names are the keys and the values are the values.
def get_secret(query="mysql", fn = "secrets.txt"):
    
    #requires that the user have a file called 'secrets.txt' where the lines in it are:
    #mysql_un=username
    #mysql_pw=password
    #mysql_hn=hostname
    #mysql_db_name=db_name

    dir_path = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(dir_path, fn)
    my_dict = {}
    with open(fn, "r") as f:
        '''---Going line by line in file looking for query---'''
        for line in f:
            desc_delim = line.find("_")
            if desc_delim == -1:
                '''---If format is not as expected, then skip that line and print warning to console---'''
                print(f"WARNING: Should have '_' in this line:\n{line}\n")

            if line.find(query) > -1:
                '''---If query is found, parse the line---'''
                key_delim = line.find("=")
                if key_delim == -1:
                    '''---If format is not as expected, then skip that line and print warning to console---'''
                    print(f"WARNING: Should have '=' in this line:\n{line}\n")
                    continue

                key = line[desc_delim+1:key_delim]
                value = line[key_delim+1:].replace("\n","")
                my_dict[key] = value

    return my_dict

#Function to create a connection to the local mySQL database. Credentials can be passed in or they default to None and if host_name is left as None
#then the root_login() function will get the root login data form a file somewhere on the computer
def create_db_connection():

    secrets = get_secret()
    db_name = secrets["db_name"]
    host_name = secrets["hn"]
    user_name = secrets["un"]
    user_password = secrets["pw"]

    print(f"Connecting to '{db_name}' DB")
    connection = mysql.connector.connect(
        host=host_name,
        user=user_name,
        passwd=user_password,
        database=db_name
    )

    #MySQL Database connection successful
    return connection

#Function to check to see if jobs from last 24hrs are already in the database
def is_24_hrs( cursor ):
    cursor.execute("SELECT * FROM `history` WHERE `status` != 9 AND `my_time` >= NOW() - INTERVAL 24 HOUR")
    rows = cursor.fetchall()
    return len(rows) == 0

#Function to create my own unique job id based on the info available if unique id is not scraped
def create_job_id(job):

    #Start off wit job title, but since there will be a lot of openings for something generic like 'software engineer'
    #if that is all we look at, then I would expect a lot of collisions over time
    created_id = job.get("title")[:min(len(job.get("title")),16)] #id is 16 chars long max
    
    if job.get("post_date") is not None:
        #If post date exists, then that is a good distinguishable way to tell which posting this is
        created_id += f"{job.get("post_date").strftime('%m%d')}" #id is now 20 chars long max
    
    if job.get("url") is not None:
        #using the end of the url since I think that is usually most unique
        created_id += f"{job["url"][0 - min( len(job["url"] ), 16):]}" #id is now 36 chars long max

    if job.get("description") is not None:
        #a lot of jobs have similar descriptions to start off with, but adding this part in case we have it
        created_id += f"{job['description'][:min(len(job['description']), 28)]}" #id is now 64 chars long max

    if len(created_id) < 64 and job.get("department") is not None:
        #If there is still room to fit more into the id, add the department, then truncate to the max varchar length of 64 if needed
        created_id += job['department']
        created_id = created_id[:min(len(created_id), 64)]

    return created_id
    
#Function to send dict of jobs for a given company to mysql database
def send_to_sql( func , cursor , table_name ):
    
    #Set up variables
    assert callable(func)
    print(f"Executing {func.__name__}")
    
    s = time.perf_counter()
    job_list = func()

    if job_list is None:
        print(f"Error getting jobs for {func.__name__}")

    elif len(job_list) == 0:
        print(f"No jobs found in {func.__name__}")
        return

    cmpny_name = func.__name__[func.__name__.find("_")+1:func.__name__.rfind("_")]
    id_flag = False
    insert_list = []

    for job in job_list:

        #If there is no title for a job, then that means something else is really wrong and we are just going to thow it out
        if job.get("title") is None:
            print(f"Error, cannot find a job title for this job from {cmpny_name}. Going to skip this one...:")
            print(job)
            continue

        #Some websites don't give an id for the jobs, so this will just create one based on what we do have trying my best
        # to make it hard to repeat. If it does repeat then the new job will not be added to sql db
        if job.get("id") is None:
            id_flag = True #to notify user which companies more work needs to be done on to get a good unique identifier
            job["id"] = create_job_id(job)

        #if job post date cannot be scraped, then I'm just going to store the first day it appeared, since that should be
        #good enough assumping I'm polling daily. Any jobs already posted will not be accurate, but too bad...
        if job.get("post_date") is None:
            job["post_date"] = datetime.date.today()

        #######  MAKING SURE THAT EVERYTHING FITS FOR DEVELOPEMENT, CAN REMOVE AFTERWARDS IF WANTED  ########
        if len(job["id"]) > 64:
            '''print(job)
            print(f"WARNING - ID WAS TRUNCATED FOR THIS JOB:")'''
            job["id"] = job["id"][:64]

        if job.get("location") is not None and len(job["location"]) > 128:
            '''print(job)
            print("WARNING - LOCATIONS WAS TRUNCATED FOR THIS JOB:")'''
            job["location"] = job["location"][:128]

        if job.get("url") is not None and len(job["url"]) > 256:
            '''print(job)
            print("WARNING - URL WAS TRUNCATED FOR THIS JOB:")'''
            job["location"] = job["location"][:256]

        if job.get("department") is not None and len(job["department"]) > 64:
            '''print(job)
            print("WARNING - department WAS TRUNCATED FOR THIS JOB:")'''
            job["department"] = job["department"][:64]
        #######################################################################################################

        job["company"] = cmpny_name

        insert_list.append(
            [
                job["id"],
                job["company"],
                job["title"],
                job.get("location"),
                job.get("url"),
                job.get("department"),
                job.get("description"),
                job["post_date"]
            ]
        )
        
    #Create the SQL query to format and insert the data into the db
    list_to_table( insert_list, table_name, cursor)

    if id_flag:
        print(f"WARNING: {cmpny_name} jobs are not being parsed with an ID, this should be addressed since it is prone to errors downstream")
    
    cursor.execute("INSERT INTO `performance`(`func`, `tot_time`, `num_jobs`,`call_date`) VALUES (%s,%s,%s,%s);", [func.__name__, int((time.perf_counter()-s)*1000000), len(job_list), datetime.datetime.now()])

    return

#send any error info to database for logging
def log_errors( cursor, errors, history_id):

    #Create the SQL query to format and insert the data into the db
    for error in errors: 
        error[3] = f"{type(error[3]).__name__} - {str(error[3])}"

    #send data in errors list to errors table
    list_to_table(errors, "errs", cursor)

    if len(errors) > 0:
        return 1
    
    return 0

#Function which will query the database for any new jobs since last time. Or caller can pass in an int 'days' to ask for jobs posted within that timeframe
def print_latest_jobs(days = -1, cursor = None):

    #If connection is not passed in from caller, create and manage one locally here
    local_con = False
    if cursor is None:
        con = create_db_connection()
        cursor = con.cursor()
        local_con = True
        
    try:
        assert isinstance(days, int)
    except AssertionError as ae:
        print("Error, days must be an int, doing nothing")
        raise ae

    if days == -1:

        cursor.execute("SELECT my_time FROM `history` ORDER BY my_time DESC LIMIT 1")
        last_pull = cursor.fetchall()[0][0]
        days = (datetime.datetime.now() - last_pull).days

    query_string = f"""
                    SELECT title, company, url
                    FROM pdx_hw_jobs.jobs 
                    WHERE post_date >= CURRENT_DATE() - INTERVAL {days} DAY
                    ORDER BY post_date DESC;
                    """
    cursor.execute(query_string)
    resp = cursor.fetchall()
    
    if local_con:
        con.close()
    
    #Lengths of each of the varchars in the table
    JOB_LEN = 64
    COMPANY_LEN = 32
    URL_LEN = 256

    print(f"+{"-"*(JOB_LEN+COMPANY_LEN+URL_LEN)}+")
    for job in resp:
        formatted_title = job[0] if len(job[0])<JOB_LEN else job[0][:JOB_LEN-3]+"..."
        print(f"|{formatted_title}{" "*(JOB_LEN-len(job[0]))}|{job[1]}{" "*(COMPANY_LEN-len(job[1]))}|{job[2]}{" "*(URL_LEN-len(job[2])) if job[2] is not None else " "*(URL_LEN-4)}  |")

#function to send a list of values to a specific table in the database
def list_to_table(insert_list, table_name, cursor):
    
    if len(insert_list) == 0:
        return

    history_alias_list = ""
    for _ in range(len(insert_list[0])):
        history_alias_list += "%s,"
    write_query = f"INSERT IGNORE INTO `{table_name}` VALUES({history_alias_list[:-1]});"
    cursor.executemany(write_query, insert_list)

def test():

    t0_con = create_db_connection()
    t0_cur = t0_con.cursor()

if __name__ == "__main__":
    
    #Setting up variables to check if it is time to look for jobs again
    s = time.perf_counter()
    t0_con = create_db_connection()
    t0_cur = t0_con.cursor()

    table_name = "jobs"

    user_question = f"Using the PRODUCTION {table_name} table? ('Y' to continue, anything else to exit)"
    if table_name == "jobs" and input(user_question).lower() != 'y':
        exit("Scrape cancelled, exiting!")

    user_question = "It has been less than 24hrs since last pull, would you like to pull again anyway? ('Y' for yes, anything else for no)"
    if is_24_hrs(t0_cur) is False and input(user_question).lower() != 'y':
        exit("Scrape cancelled, exiting!")

    #Might be worthwhile to write some code to make sure the jobs are optimally scheduled. I put the jobs that take the longest
    #at the front of the list so that way those can all get done in parallel and balance the temporal load between threads
    job_queue = [
        #fetch_tsmc_jobs,
        #fetch_intel_jobs,
        #fetch_amat_jobs,
        #fetch_amd_jobs,
        #fetch_apple_jobs,
        #fetch_autodesk_jobs,
        #fetch_cisco_jobs,
        #fetch_celestica_jobs,
        #fetch_ampere_jobs,
        #fetch_compunet_jobs,
        #fetch_google_jobs,
        #fetch_hp_jobs,
        fetch_analog_devices_jobs,
        fetch_kla_jobs,
        fetch_lam_jobs,
        fetch_lattice_jobs,
        fetch_marvell_jobs,
        fetch_microchip_jobs,
        fetch_microsoft_jobs,
        fetch_nfi_jobs,
        fetch_nvidia_jobs,
        fetch_onsemi_jobs,
        #fetch_qorvo_jobs,
        #fetch_qualcomm_jobs,
        #fetch_ralliant_jobs,
        #fetch_siemens_jobs,
        #fetch_siltronic_jobs,
        #fetch_skyworks_jobs,
        #fetch_vgems_jobs,
    ]

    #Setting up variables to keep track of theads and any errors that occur in them
    errs = []
    num_threads = 4
    conns = [t0_con]
    crsrs = [t0_cur]
    for i in range(num_threads-1):

        temp_con = create_db_connection()
        crsrs.append(temp_con.cursor())
        conns.append(temp_con)

    #Adding this scrape to the history database, code 9 means no error but scrape not completed yet
    t0_cur.execute (f"INSERT INTO history VALUES (NOW(),%s,NULL)", (9,))
    history_id = t0_cur.lastrowid
    t0_con.commit()

    with ThreadPoolExecutor(max_workers=num_threads) as ex:
        
        threads = []
        funcs = []
        for i in range(num_threads):

            job = job_queue.pop(0)
            threads.append(ex.submit(send_to_sql,job, crsrs[i], table_name))
            funcs.append(job.__name__)

        #giving the threads time to do work
        time.sleep(0.5)

        #Work through the job queue making sure to keep pool of threads full
        while len(job_queue) > 0:
            
            print("working threads: ",funcs)
            #check if any threads are done, if so, replace it with the next one in the queue
            for i, thread in enumerate(threads):

                if thread.done():

                    if thread.exception():
                        
                        #If I really wanted this to be good, I would add handling for common exception here or crash out all threads
                        errs.append( [ history_id, i, funcs[i], thread.exception() ] )
                        print(f"Thread {i} threw exception while performing {funcs[i]}\n: {thread.exception()}\n")

                    # Make sure we dont't pop off an empty queue during thread processing
                    try: 
                        job = job_queue.pop(0)
                    except IndexError:
                        break

                    threads[i] = ex.submit(send_to_sql, job, crsrs[i], table_name)
                    funcs[i] = job.__name__

            time.sleep(0.5)

        print("Job queue empty, just waiting on the last jobs to finish")

        #When no more jobs in queue, wait for the rest of the threads to finish without checking for new jobs (there are none!)
        while len(threads) > 0:
            
            #Check remaining threads to see if any are done. Has to be done in reverse so that when threads are popped, no index errors occur
            for i in reversed( range( len(threads ) ) ) :
                thread = threads[i]
                
                if thread.done():

                    if thread.exception():

                        errs.append( [ history_id, i, funcs[i], thread.exception() ] )
                        print(f"Thread {i} threw exception while performing {funcs[i]}\n: {thread.exception()}\n")

                    threads.pop(i)
                    funcs.pop(i)

            time.sleep(0.5)

    #Update history to show that the scrape finished. 0 means with no errors, 1 means completed with errors
    t0_cur.execute (f"UPDATE history SET status = { log_errors( t0_cur, errs, history_id ) } WHERE id = { history_id }")
    print("Done scraping!")
    print_latest_jobs( cursor=t0_cur )

    #Close all open mysql connections
    for i, conn in enumerate(conns): 
        conn.commit()
        if i > 0: conn.close()
    