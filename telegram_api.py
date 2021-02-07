import requests

# telegram bot api test
chat_id = '678478220'
base_url = "https://api.telegram.org/bot1640815585:AAHancwBwckiHtRFTc2g78akroVDYTtU1E4"
sendmessage_path = "/sendMessage"

#url = "https://api.telegram.org/bot1640815585:AAHancwBwckiHtRFTc2g78akroVDYTtU1E4/getUpdates"

def SendMessage(text):
    #make query string
    querystring = {"chat_id":chat_id,"text":text}
    url = base_url + sendmessage_path
    response = requests.request("GET", url, params=querystring)
    if response.status_code == 200:
        print('SendMessage is successed')
        print(response.json())