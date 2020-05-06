from library.choose_account_from_hi import main as choose_account
# from library.async_semaphore import *
from dotenv import load_dotenv
from halo import Halo
from codetiming import Timer
from bs4 import BeautifulSoup
import pandas as pd 
import time
import os
from test_platform import *
import requests
# Default directories where input and output data located
from library.cm_download import CampaignMonitorClient

load_dotenv()

INPUT_DIR_NAME = 'input'
OUTPUT_DIR_NAME = 'output'

# Caution: Remember to open VPN before running this program

# Constants, global variables
# NEW_DATA represent the data we want to check quality and do cleaning up
# You should have such file in input directory
NEW_DATA = "" # you should change name accordingly, excel or csv is okay!

# Credentials
CSE_EMAIL = os.getenv("CSE_EMAIL") 
CSE_PASSWORD = os.getenv("CSE_PASSWORD") 
DV_API_KEY = os.getenv("DV_API_KEY")
HIIQ_API_KEY = os.getenv("HIIQ_API_KEY")
HIIQ_URL = os.getenv("HIIQ_URL")

def clean_data(current_users):
    global NEW_DATA

    file_name, file_extension = NEW_DATA.split(".")[0], NEW_DATA.split(".")[1]
    if file_extension == 'csv':
        new_user_data = pd.read_csv(INPUT_DIR_NAME + '/' + NEW_DATA)
    elif file_extension == 'xlsx' or file_extension == 'xls':
        new_user_data = pd.read_excel(INPUT_DIR_NAME + '/' + NEW_DATA)
    else:
        return -1, "error: file_extention is not supported: " + file_extension
    
    # check email header exist
    is_no_email_header = True
    email_header = None
    for header in list(new_user_data.columns):
        formatted_header = header.lower().strip()
        if formatted_header.find("email") != -1 or formatted_header.find("e-mail"):
            email_header = header
            is_no_email_header = False
            break
    
    if is_no_email_header is True:
        return -1, "error: no email header/column found in your file " + NEW_DATA

    new_emails = new_user_data[email_header] #E-Mail or Email
    new_emails = new_user_data.rename(columns={email_header: "Email"})['Email']
    print("Number of users in the new file: ", len(new_emails))    
    # new_emails.sort_index(inplace=True)
    new_emails = new_emails.str.lower()
    new_emails = new_emails.str.strip()
    new_emails.drop_duplicates(keep="last", inplace=True)
    print("Number of users after dedup: ", len(new_emails))
    new_emails.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "_removed_dup.csv", header=True, index=False)

    """get current existing users"""
    current_users['Email'] = current_users['Email'].str.lower()
    current_users['Email'] = current_users['Email'].str.strip()
    merged = current_users.merge(new_emails, how="right", indicator=True)
    merged.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "compared_with_currentdb.csv", index=False, columns=["Email", "Status"])

    new_users = merged[merged['_merge']=='right_only']
    existing_sub = merged[merged['Status']=='sub']
    existing_unsub = merged[merged['Status']=='unsub']
    suppressed = merged[merged['Status']=='excluded']

    existing_sub.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "_existing_sub.csv", index=False)
    
    print("Number of new users: ", len(new_users), end=", ")
    print("along with %s existing sub, %s unsub, %s cleaned users" %(len(existing_sub), len(existing_unsub), len(suppressed)))
    
    new_users = pd.DataFrame(new_users['Email'])
    new_users.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "_new_users.csv", index=False)
    sample_bad_emails = pd.read_csv("bad_emails.csv")
    new_users['Domain'] = new_users['Email'].str.split('@').str[1]
    merged = sample_bad_emails.merge(new_users, how="right", indicator=True, on="Domain")
    good_emails = merged[merged['_merge']=='right_only']
    print("Number of user after remove blacklisted domain: ", len(good_emails))
    good_emails = good_emails['Email']
    good_emails.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "_to_cse2.csv", index=False, header=True)
    bad_emails  = merged[merged['_merge']=='both']
    bad_emails.to_csv(OUTPUT_DIR_NAME + "/" + file_name + "_blacklisted.csv", index=False, header=True, columns=["Email", "Domain"])

def upload_cse():
    # login to cse tool
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=5)
    s.mount("https://", a)    
    res = s.get('https://cse-prod2.ematicsolutions.com/login')
    cookies = res.cookies
    soup = BeautifulSoup(res.content, 'html.parser')
    tag = soup.body.find("input", {"name":"_token"})
    token = tag.attrs['value']

    data = {
        "_token": token,
        "email": CSE_EMAIL,
        "password": CSE_PASSWORD, 
    }
    response = requests.post("https://cse-prod2.ematicsolutions.com/login", 
                            data=data, cookies=cookies)

    if response.url  == "https://cse-prod2.ematicsolutions.com/home":    
        print("✔ CSE tool login succeeded")
    else:
        print("✔ CSE tool login failed")
        exit()

    cookies = response.cookies
    res = s.get("https://cse-prod2.ematicsolutions.com/cleaned-emails-scan/create", cookies=cookies)
    cookies = res.cookies
    soup = BeautifulSoup(res.content, 'html.parser')
    token = soup.body.find("input", {"name":"_token"}).attrs['value']

    data = {'_token': token, 
                'email_column_ordinal': '1',
                'header_row': '1'
            }
    cse_file = NEW_DATA.split(".")[0] + "_to_cse2.csv"
    files = {
        "csv_file": open(OUTPUT_DIR_NAME + "/" + cse_file, 'r')
    }
    scan = requests.post("https://cse-prod2.ematicsolutions.com/cleaned-emails-scan", 
                        data=data, cookies=cookies, files=files
                        )
    print("✔ CSE cleaned emails scan created: ", scan.request.url)

    taskUrl = scan.request.url 
    task = requests.get(taskUrl + "/status" ,cookies=cookies)
    while task.json()['progress'] != '100.00':
        print("✔ Clean processed: %s", task.json()['progress'], "...")
        task = requests.get(scan.request.url + "/status",cookies=cookies)
    if task.json()['progress'] == '100.00':
        print("✔ Clean processed: 100.00%")
        print("✔ CSE cleaned emails scan is done")
        
    outputUrl = "/download/output"
    cleanedUrl = "/download/cleaned"
    print('✔ Clean finished, downloading results...')

    taskUrl = scan.request.url

    file_name = cse_file.split(".")[0]
    output_file_name = file_name + "_out.csv"
    clean_file_name = file_name + "_cleaned.csv"

    output_res = requests.get(taskUrl + outputUrl, cookies=cookies)
    f = open(OUTPUT_DIR_NAME + "/" + output_file_name, mode="wb")
    f.write(output_res.content)
    f.close()

    cleaned_res = requests.get(taskUrl + cleanedUrl, cookies=cookies)
    f = open(OUTPUT_DIR_NAME + "/" + clean_file_name, mode="wb")
    f.write(cleaned_res.content)
    f.close()
    spinner.succeed("Done validation")

    print("Total email addresses: ", task.json()['input_count'])
    print("Valid email addresses: ", task.json()['output_count'])
    print("Cleaned email addresses: ", task.json()['cleaned_count'])
    print('✔ Clean results downloaded.');        

def getDvScore():
    spinner = Halo(text="Checking dv score  of the cleaned data by cse2 tool", spinner='dots', text_color="grey")
    spinner.start()
        
    file = NEW_DATA.split(".")[0] + "_to_cse2_out.csv"
    url = 'https://dv3.datavalidation.com/api/v2/user/me/list/create_upload_url/'
    params = '?name=' + file + '&email_column_index=0&has_header=0&start_validation=false'     
    headers = { 'Authorization': 'Bearer ' + DV_API_KEY }
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=3)
    s.mount("https://", a)    
    res = s.get(url+params, headers=headers)
    upload_csv_url = res.json()    
    files = {
        'file': open(OUTPUT_DIR_NAME + "/" + file, 'rb')
    }
    # list_id = requests.post(upload_csv_url, headers=headers, files=files)
    list_id = s.post(upload_csv_url, headers=headers, files=files)
    dv_result_url = 'https://dv3.datavalidation.com/api/v2/user/me/list/' + list_id.json()
    # dv_result = requests.get(dv_result_url, headers=headers).json()
    dv_result = s.get(dv_result_url, headers=headers).json()
    while dv_result['status_value'] == 'PRE_VALIDATING':
        dv_result = requests.get(dv_result_url, headers=headers).json()
        spinner.info("Status percent complete: " + str(dv_result['status_percent_complete']))
        time.sleep(5) # sleep 5 seconds
    try:
        percent = lambda count: round((count / dv_result['subscriber_count']),2) * 100
        
        spinner.succeed("Done checking dv score")
        print("The grade summary is: ")
        for score_name, score_value in dv_result['grade_summary'].items():
            print('%-3s : ' %(score_name) + str(percent(score_value)))
    except:
        if (dv_result['subscriber_count'] == 0):
            print("Empty list of emails were sent for dv validation!")
            print("Perhaps no new email to check dv?")
            print("Program terminated")
            return 0

if __name__ == "__main__":
    # turn on vpn
    page_size = 1000    
    connectVPN()
    time.sleep(20)
    # Select account    
    env_file = open(".env", mode="r")
    env_data = env_file.readlines()    
    exit_code, account = choose_account(HIIQ_API_KEY, HIIQ_URL)
    if exit_code == -1:
        exit(code=-1)

    api_key, client_id = account['api_key'], account['client_id']
    # turn off vpn
    disconnectVPN()

    # ## Fetching the contacts    
    t = Timer(name="class", text="Time to fetch the contacts: {seconds:.1f} seconds")
    spinner = Halo(text="Fetching contacts via API ..", spinner='dots', text_color="grey")
    spinner.start()        
    t.start()

    cm_client = CampaignMonitorClient(client_id,api_key,page_size)
    suppresion_list,suppresion_numb = cm_client.fetchAllSuppressedUsers()
    
    contact_list = cm_client.fetchContactList()[0][0]

    active_list,active_numb = cm_client.fetchAllSubscribers(contact_list)

    unsub_list,unsub_numb = cm_client.fetchAllUnSubscribers(contact_list)


    excluded_df = pd.DataFrame({
        "Email": suppresion_list,
        "Status": "excluded"
    })

    active_df = pd.DataFrame({
        "Email": active_list,
        "Status": "sub"
    })

    unsub_df = pd.DataFrame({
        "Email": unsub_list,
        "Status": "unsub"
    })
    cm_data = active_df.append(unsub_df).append(excluded_df)

    cm_data.to_csv(OUTPUT_DIR_NAME + "/current_cm_data.csv", index=False)
    
    spinner = spinner.succeed(text="Downloaded all contacts")
    t.stop()

    spinner.start("Processing the data")
  

    # contacts.to_csv(OUTPUT_DIR_NAME + "/current_mj_db.csv",index=False)

    spinner.succeed(text="Done processing the data")

    clean_data(cm_data)

    # turn on vpn
    connectVPN()
    time.sleep(20)
    upload_cse()
    # turn off vpn
    disconnectVPN()
    getDvScore()
    spinner.succeed("Program completed!")

    # This block can be commented/removed if you don't want to connect VPN again
    print("Reconnecting to VPN again")
    connectVPN()
