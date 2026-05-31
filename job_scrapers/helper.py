from datetime import datetime, timedelta

#One place to check if a job is too old to apply to it
def is_old(check_time):
    
    # Age threshold: jobs older than this many months are considered stale
    MONTHS = 3

    if type(check_time) is not datetime:
        print("check_time must be a datetime object.")
        return False

    # Respect the timezone of the input datetime if it has one
    now = datetime.now(check_time.tzinfo) if check_time.tzinfo else datetime.now()

    # Compare against a rolling cutoff calculated from the current time
    if check_time < now - timedelta(days=MONTHS*30):
        #print(f"Reached jobs older than {MONTHS} months: {check_time.strftime('%m-%d-%Y')}.")
        return True
    return False

def print_jobs(job_list):
    for job in job_list:
        for k,v in job.items():
            print(f"{k} {v}")
        print("-"*20)