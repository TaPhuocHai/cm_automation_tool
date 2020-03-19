import asyncio
import aiohttp


class Unsuppresser:
    def __init__(self, email_list=[], client_id=None, api_key=""):
        self.email_list = email_list
        self.client_id  = client_id
        self.api_key    = api_key

    async def unsuppress(self, url, session, auth, email):
        async with session.put(url, auth=auth) as response:
            # res = await response.read()
        
            print("Unsuppresed %s" %(email), response.status)
            # for c in result['Data']:
            
            #     RECIPIENT_LIST.append([c['ContactID'], c['IsUnsubscribed'], c['ListName']])

    async def boundUnsuppress(self, sem, url, session, auth, email):
        # Getter function with semaphore
        async with sem:
            await self.unsuppress(url, session, auth, email)

    async def unsunpress(self):
        """
        Wrapper of async fetch snippet
        """
        # Create the queue of work
        tasks = []
        sem = asyncio.Semaphore(10000) # safe number of concurrent requests
        auth = aiohttp.BasicAuth(self.api_key, "")
        async with aiohttp.ClientSession() as session:
            for email in self.email_list:
                url = "https://api.createsend.com/api/v3.2/clients/%s/unsuppress.json?email=%s"%(self.client_id, email)
                task = asyncio.ensure_future(self.boundUnsuppress(sem, url, session, auth, email))
                tasks.append(task)
            
            responses = asyncio.gather(*tasks)
            await responses


