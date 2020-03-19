import requests

def getClientList(API_KEY):
    response = requests.get("https://api.createsend.com/api/v3.2/clients.json", auth=(API_KEY, ""))
    clients = {}
    try:
        for eachClient in response.json():
            ClientID, Name = eachClient['ClientID'], eachClient['Name']
            clients[Name] = ClientID
        
        return clients
    except:
        print("Error occurred with the requests")
        print("Please check your API_KEY")
        print("Program terminated")
        exit(-1)

def importSuppressionList(API_KEY, clientid, email_list):
    '''
    This module aims to bulk import multiple emails into Suppression list
    ----------------------------------------------------------------------------
    Comment: Mar 15, 2020
    In case emails exist, it still return 200 status code
    '''
    url = "https://api.createsend.com/api/v3.2/clients/%s/suppress.json" % (clientid)
    payload = {
        "EmailAddresses": email_list
    }
    response = requests.post(url, auth=(API_KEY, "", ), headers={'User-Agent': 'Mozilla/5.0', 'Connection':'close'}, json=payload)
    
    if response.status_code == 200:
        return response.status_code, "Import email(s) into Suppression list successfully"
    else:
        if response.status_code == 504: # It still works
            return 504, "Code 504, Gateway Time-out. Please check the suppressed emails on CM after the program finishes."
        print("Error happened while importing")
        return response.status_code, str(response.content)