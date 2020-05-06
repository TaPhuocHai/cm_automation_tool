import json
import requests
import pandas as pd

class CampaignMonitorClient:
    """
        Campaign Monitor Client Class.
    """
    def __init__(self, client_id, api_key, page_size):
        """Initizalize CM client with client id, api key, and page size"""
        self.client_id = client_id
        self.api_key   = api_key
        self.page_size = page_size
        self.suppressed_users = None
        self.subscribers = None
        self.unsubscribers = None
    
    def __fetchSuppressedUsers(self, page, page_size, client_id, verbose=False): 
        """
        Fetch suppressed users
        Parameters:
        - page: page number (if there are more one page, we need to call multitimes to get all suppressed number)
        - page_size: number of maximum users each response returns
        - client_id: Client ID of the Campaign Monitor
        - verbose:  If set to True, the function keeps the TotalNumberOfRecords and Number Og Pages in the return value tuple. This is helpful to know how many users and requests required to call Campaign Monitor API
        Return a list of unsubsribers if verbose is False
        Return a tupple of a list of unsubsribers, TotalNumberOfRecords, NumberOfPages  if verbose is True
        """
        url = f'https://api.createsend.com/api/v3.2/clients/{client_id}/suppressionlist.json?page={page}&pagesize={page_size}'
        suppression_list = []
        r = requests.get(url, auth=(self.api_key, ""))
        data = r.json()
        for item in data['Results']:
            suppression_list.append(item["EmailAddress"])

        if verbose == True:
            TotalNumberOfRecords = data['TotalNumberOfRecords']
            NumberOfPages = data['NumberOfPages']
            return suppression_list, TotalNumberOfRecords, NumberOfPages

        return suppression_list

    def __fetchActiveUsers(self, page, page_size, list_id, client_id, verbose=False):
        """
        Fetch fetchActiveUsers users
        Parameters:
        - page: page number (if there are more one page, we need to call multitimes to get all suppressed number)
        - page_size: number of maximum users each response returns
        - client_id: Client ID of the Campaign Monitor
        - verbose:  If set to True, the function keeps the TotalNumberOfRecords and Number Og Pages in the return value tuple. This is helpful to know how many users and requests required to call Campaign Monitor API
        Return a list of unsubsribers if verbose is False
        Return a tupple of a list of unsubsribers, TotalNumberOfRecords, NumberOfPages  if verbose is True
        """    
        url = f"https://api.createsend.com/api/v3.2/lists/{list_id}/active.json?&page={page}&pagesize={page_size}"
        active_list = []
        r = requests.get(url, auth=(self.api_key, ""))
        data = r.json()
        for item in data['Results']:
            active_list.append(item["EmailAddress"])

        if verbose == True:
            TotalNumberOfRecords = data['TotalNumberOfRecords']
            NumberOfPages = data['NumberOfPages']

            return active_list, TotalNumberOfRecords, NumberOfPages

        return active_list

    def __fetchUnsubscribedUsers(self, page, page_size, list_id, client_id, verbose=False):
        """
        Fetch fetchActiveUsers users
        Parameters:
        - page: page number (if there are more one page, we need to call multitimes to get all suppressed number)
        - page_size: number of maximum users each response returns
        - client_id: Client ID of the Campaign Monitor
        - verbose:  If set to True, the function keeps the TotalNumberOfRecords and Number Og Pages in the return value tuple. This is helpful to know how many users and requests required to call Campaign Monitor API
        Return a list of unsubsribers if verbose is False
        Return a tupple of a list of unsubsribers, TotalNumberOfRecords, NumberOfPages  if verbose is True
        """        
        url = f"https://api.createsend.com/api/v3.2/lists/{list_id}/unsubscribed.json?&page={page}&pagesize={page_size}"
        unsub_list = []
        r = requests.get(url, auth=(self.api_key, ""))
        data = r.json()
        for item in data['Results']:
            unsub_list.append(item["EmailAddress"])

        if verbose == True:
            TotalNumberOfRecords = data['TotalNumberOfRecords']
            NumberOfPages = data['NumberOfPages']

            return unsub_list, TotalNumberOfRecords, NumberOfPages

        return unsub_list


    def fetchContactList(self):
        """
        Fetch all available contact list in the Campaign Account
        Return a list of contact lists
        """
        url = f'https://api.createsend.com/api/v3.2/clients/{self.client_id}/lists.json'
        contact_lists = []
        r = requests.get(url, auth=(self.api_key, ""))
        data = r.json()
        for contact_list in data:
            contact_lists.append((contact_list['ListID'], contact_list['Name'])) # return tuples
        return contact_lists

    def fetchAllSuppressedUsers(self):
        # print("Start fetching all suppressed users")
        page = 1
        global_suppression_list,TotalNumberOfRecords, NumberOfPages = self.__fetchSuppressedUsers(page, self.page_size, self.client_id, verbose=True)
        if NumberOfPages > 1:
            for page in range(2, NumberOfPages+1):
                global_suppression_list += self.__fetchSuppressedUsers(page, self.page_size, self.client_id, verbose=False)
        if len(global_suppression_list) != TotalNumberOfRecords:
            print("Warning their is unmatched between the downloaded suppression list and the one in Campaign Monitor")        
        print("Done fetching all suppressed users")
        return global_suppression_list, TotalNumberOfRecords
        # pd.DataFrame(data=global_suppression_list, columns=['Email Addresss']).to_csv("suppression.csv")

    
    def fetchAllSubscribers(self, list_id):
        # print("Start fetching all subscribers")
        page = 1
        active_list,TotalNumberOfRecords, NumberOfPages = self.__fetchActiveUsers(page, self.page_size, list_id, self.client_id, verbose=True)
        if NumberOfPages > 1:
            for page in range(2, NumberOfPages+1):
                active_list += self.__fetchActiveUsers(page, self.page_size, list_id, self.client_id, verbose=False)
        
        print("Done fetching all subscribers")
        return active_list, TotalNumberOfRecords

    def fetchAllUnSubscribers(self, list_id):
        # print("Start fetching all unsubscribers")
        page = 1
        active_list,TotalNumberOfRecords, NumberOfPages = self.__fetchUnsubscribedUsers(page, self.page_size, list_id, self.client_id, verbose=True)
        if NumberOfPages > 1:
            for page in range(2, NumberOfPages+1):
                active_list += self.__fetchUnsubscribedUsers(page, self.page_size, list_id, self.client_id, verbose=False)
        
        print("Done fetching all unsubscribers")
        return active_list, TotalNumberOfRecords

"""
Demo how the module can be ran
cm_client = CampaignMonitorClient(client_id,api_key,page_size)
suppresion_list,suppresion_numb = cm_client.fetchAllSuppressedUsers()

pd.DataFrame(data=suppresion_list, columns=['Email Addresss']).to_csv("suppression.csv")

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

cm_data.to_csv("cm_data.csv")
"""


