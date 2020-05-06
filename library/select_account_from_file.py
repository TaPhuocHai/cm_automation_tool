import base64
import requests
import json

from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit import prompt


def get_accounts(data):
    display_keys = []
    for k in data.keys():
        display_keys.append((k, k))
    results_array = checkboxlist_dialog(
        title="Account selection dialog",
        text="Please select the account to fetch nondeliveries+spam users?",
        values= display_keys
    ).run()

    return 1,results_array


def main(data):
    exit_code, selected_accounts = get_accounts(data)
    if exit_code == -1:
        print("Program terminated..")
        return -1,{}
    
    print("You've selected acccount %s" %(selected_accounts))
    
    return 1, selected_accounts
    
# if __name__ == "__main__":
#     print(main())
