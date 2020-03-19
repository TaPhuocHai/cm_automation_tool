import requests 
import pandas as pd
from prompt_toolkit import prompt
from halo import Halo
import os.path
from os import path
import glob
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from library.cm_utilities import importSuppressionList

from codetiming import Timer
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SUPPRESSING_API_KEY") 
CLIENT_ID = os.getenv("SUPPRESSING_CLIENT_ID") 


if __name__ == "__main__":

    spinner = Halo(spinner='dots')
    spinner.start('Check if suppression_list ..')
    if path.exists("suppression_list"):
        spinner.succeed("suppression_list exists!")
    else:
        spinner.fail("suppression_list does not exists!")
        exit(-1)

    suppression_files = glob.glob("suppression_list/*.csv")
    suppression_files += glob.glob("suppression_list/*.xlsx")
    AccountCompleter = WordCompleter(suppression_files,
                                ignore_case=False)
    checked = False
    while checked is False:
        user_input = prompt('Choose file from suppression_list: ',
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
            
            confirm = prompt("Enter y or n to confirm proceed suppression process: ")
            while True:
                if confirm == 'y' or confirm == 'n':
                    break
                else:
                    confirm = prompt("Enter y or n to confirm proceed suppression process: ")
            if confirm == 'y':
                checked = True

    file[user_input] = file[user_input].sort_values()
    email_list = list(file[file.notnull()][user_input])

    print("Number of emails to be suppressed: ", len(email_list))
    

    LIMIT = 5000 # Number of email each time suppressing
    start = 0
    end = LIMIT
    t = Timer(name="class", text="Time for suppressing contacts: {seconds:.1f} seconds")
    t.start()
    
    if len(email_list) > LIMIT:
        while end <= len(email_list):
            print("Email address from index %s to %s are being processed " %(start, end))
            status_code, msg = importSuppressionList(API_KEY, CLIENT_ID, email_list[start:end])
            print("Status code: %s." % (str(status_code)) ,msg)
            start = end
            end += LIMIT
    else:
        print("Email address from index %s to %s are being processed " %(start, end))
        status_code, msg = importSuppressionList(API_KEY, CLIENT_ID, email_list[start:end])        
        print("Status code: %s." % (str(status_code)) ,msg)
        
    t.stop()
    
    