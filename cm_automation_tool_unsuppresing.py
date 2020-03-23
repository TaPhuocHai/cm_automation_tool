import os
from os import path
import glob
import asyncio
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
import requests
import pandas as pd
from prompt_toolkit import prompt
from halo import Halo
from codetiming import Timer
from dotenv import load_dotenv
from library.cm_utilities import getClientList
from library.async_unsuppress import Unsuppresser
load_dotenv()


API_KEY = os.getenv("UNSUPPRESSING_API_KEY") 
CLIENT_ID = os.getenv("UNSUPPRESSING_CLIENT_ID") 


if __name__ == "__main__":
    # Check if folder unsuppression_list exists
    spinner = Halo(spinner='dots')
    spinner.start('Check if suppression_list ..')
    if path.exists("unsuppression_list"):
        spinner.succeed("unsuppression_list exists!")
    else:
        spinner.fail("unsuppression_list does not exists!")
        exit(-1)

    # Load all csv and xlsx files in unsuppression_list folder
    suppression_files = glob.glob("unsuppression_list/*.csv")
    suppression_files += glob.glob("unsuppression_list/*.xlsx")    

    # Let user choose file among the existing files
    AccountCompleter = WordCompleter(suppression_files, ignore_case=False)
    checked = False
    while checked is False:
        user_input = prompt('Choose file from unsuppression_list: ',
                                history=FileHistory('history.txt'),
                                auto_suggest=AutoSuggestFromHistory(),
                                completer=AccountCompleter,
                            )
        if user_input.find(".csv") == -1 and user_input.find("xlsx") == -1:
            spinner.fail("File chosen is not either a csv or xlsx")
        else:
            if user_input.find(".csv") != -1:
                file = pd.read_csv(user_input)
            elif user_input.find(".xlsx") != -1:
                file = pd.read_excel(user_input)
            checked = True
    spinner.succeed("File is loaded")

    # Lookup email/e-mail header(s) in the selected file
    is_no_email = True
    email_headers = []
    file_cols= list(file.columns)    
    for indx, col in enumerate(file_cols):
        if col.lower().strip().find("email") != -1 or col.lower().strip().find("e-mail") != -1:
            email_headers.append((indx, col)) # tuple would be fine, no need a hash-like data structure!
            is_no_email = False
    columns = [h[1] for h in email_headers]
    if len(columns) > 0:
        print("Found (these) email header(s): ")
        print(columns)
    else:
        spinner.fail("No email header found!")        
        spinner.fail("Program terminated unsuccessfully")
        exit(-1)

    # Let user to choose header
    ColumnCompleter = WordCompleter(columns,
                                ignore_case=False)
    checked = False
    while checked is False:
        user_input = prompt('Choose email column from selected file: ',
                                history=FileHistory('history_columns.txt'),
                                auto_suggest=AutoSuggestFromHistory(),
                                completer=ColumnCompleter,
                            )
        if user_input not in set(file.columns):
            print("%s does not exists as a column name" %(user_input))
        else:
            print("%s is valid column name" %(user_input))            
            confirm = prompt("Enter y or n to confirm proceed unsuppression process: ")
            while True:
                if confirm == 'y' or confirm == 'n':
                    break
                else:
                    confirm = prompt("Enter y or n to confirm proceed unsuppression process: ")
            if confirm == 'y':
                checked = True



    t = Timer(name="class", text="Time for unsuppressing contacts: {seconds:.1f} seconds")
    
    file[user_input] = file[user_input].sort_values()
    email_list = list(file[file.notnull()][user_input])
    
    # unsuppresser = Unsuppresser(email_list= email_list, client_id=CLIENT_ID, api_key=API_KEY)

    print("Number of emails to be unsuppressed: ", len(email_list))
    t.start()
    url = url = "https://api.createsend.com/api/v3.2/subscribers/%s/import.json"%("2c3b174c69438de30696dda5e388a58a")

    subscribers = []
    for e in email_list:
        subscribers.append({"EmailAddress": e,"ConsentToTrack":"Yes"})

    payload = {
        "Subscribers": subscribers,
        "Resubscribe": True,
        "QueueSubscriptionBasedAutoResponders": False,
        "RestartSubscriptionBasedAutoresponders": False
    }
    res  = requests.post(url, auth=(API_KEY,""), json=payload)
    print(res.json())
    # asyncio.run(unsuppresser.unsunpress())
    t.stop()
    print()
    
    