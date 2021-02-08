import requests

# telegram bot api test
base_url = "https://api.telegram.org/bot1640815585:AAHancwBwckiHtRFTc2g78akroVDYTtU1E4"
sendmessage_path = "/sendMessage"
getUpdates_path = "/getUpdates"

#url = "https://api.telegram.org/bot1640815585:AAHancwBwckiHtRFTc2g78akroVDYTtU1E4/getUpdates"

def GetChatIdList():
    url = base_url + getUpdates_path
    response = requests.request("GET", url)
    updates = response.json()

    idlist = set()
    for msg in updates["result"]:
        idlist.add(msg["message"]["chat"]["id"])
    
    return idlist

def SendMessage(text):
    #make query string
    chatids = GetChatIdList()
    for id in chatids:
        querystring = {"chat_id":id,"text":text}
        url = base_url + sendmessage_path
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            print('SendMessage is successed')
            print(response.json())