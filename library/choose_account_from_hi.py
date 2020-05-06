from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from log_symbols import LogSymbols
import base64
import requests

def get_accounts(hi_api_key, hi_api_url):

    spinner = Halo(text="Fetching account via Hi-iQ api ..", spinner='dots', text_color="grey")
    spinner.start()

    headers = {
        "Authorization": "ematic-admin-apikey=" + hi_api_key
    }
    try:
        res = requests.get(hi_api_url + "/account", headers=headers, timeout=5)
    except requests.Timeout:
        print("Timeout occured. You should reset your network")
        return -1,[],[]

    if res.status_code != 200:
        print("Request to our Hi-iQ api went to errors!")
        print("Response status code: ", res.status_code)    
        return -1,[],[]

    account_list = {}
    default_list = {}

    for account in res.json()['account']:
        if account['espId'] == 2 and account['active']:
            # print("account: ", account)
            account_list[account['name']] = account['espAPIKey']
            default_list[account['name']] = account['espList']
            


    spinner.stop_and_persist(symbol=LogSymbols.SUCCESS.value, text="Done fetching account via Hi-iQ api")

    return 1,account_list, default_list

def main(hi_api_key, hi_api_url):
    exit_code, account_list, default_list = get_accounts(hi_api_key, hi_api_url)
    if exit_code == -1:
        print("Program terminated..")
        return -1,{}
    
    account_names = list(account_list.keys())
    AccountCompleter = WordCompleter(account_names,
                                ignore_case=False)
    while 1:
        user_input = prompt('Choose your account: ',
                            history=FileHistory('history.txt'),
                            auto_suggest=AutoSuggestFromHistory(),
                            completer=AccountCompleter,
                            )
        print(user_input)

        print("You've selected acccount %s" %(user_input))
        while 1:
            confirm = prompt("Enter y or n to continue: ")
            if confirm != 'y' and confirm != 'n':
                print("Oops! Wrong input.")
               
            else:
                break
                
        if confirm == 'y':
            if account_list.get(user_input, None) is not None:
                print("Found the account in our database")
                break
            else:
                print("The account seems like not in our database!")
                print("Try again!")

    try:
        code = account_list[user_input]
        api_pair =  base64.b64decode(code).decode("utf-8").split(":")
        
        account = user_input
        api_key, client_id = api_pair[0], api_pair[1]
        default_list_id = default_list[user_input]

        return 1, {
            "name": account,
            "api_key": api_key,
            "client_id": client_id,
            "default_list_id": default_list_id
        }
        
    except KeyError:
        print("No account name exist in our database. Please check your input!")
    except Exception:
        print("Somthing wrong happens")

