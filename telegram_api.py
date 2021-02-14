import requests
import argparse
import pickle
import os

# telegram bot api test

class TelegramBotApi:

    tele_token = ''
    base_url = "https://api.telegram.org"
    sendmessage_path = "sendMessage"
    getUpdates_path = "getUpdates"
    debug = False

    chatIdList = set()
    chatIdListPath = './chatids.txt'

    def __init__(self, token, debug=False) -> None:
        self.tele_token = token
        self.debug = debug

    def GetChatIdList(self):
        idlist = set()

        url = f"{self.base_url}/{self.tele_token}/{self.getUpdates_path}"
        print(url)
        #querystring = {"offset":-1}
        response = requests.request("GET", url)
        if response.status_code != 200:
            print('GetChatIdList error', response)
            return idlist

        updates = response.json()

        if self.debug:
            print(updates)
        
        for msg in updates["result"]:
            idlist.add(msg["message"]["chat"]["id"])
        
        return idlist

    def LoadChatIds(self):
        if not os.path.exists(self.chatIdListPath):
            return set()
            
        with open(self.chatIdListPath, 'rb') as f:
            data = pickle.load(f)
            return data

    def SaveChatIds(self, ids):
        with open(self.chatIdListPath, 'wb') as f:
            data = pickle.dump(ids, f)


    def SendMessageId(self, id, text):
        querystring = {"chat_id":id,"text":text}
        url = f"{self.base_url}/{self.tele_token}/{self.sendmessage_path}"
        response = requests.request("GET", url, params=querystring)

        if self.debug:
            print(response.json())

        if response.status_code == 200:
            print('SendMessage is successed')

    def SendMessage(self, text):
        self.chatIdList = self.LoadChatIds()

        #make query string
        chatids = self.GetChatIdList()
        chatids.update(self.chatIdList)

        self.SaveChatIds(chatids)

        for id in chatids:
            querystring = {"chat_id":id,"text":text}
            url = f"{self.base_url}/{self.tele_token}/{self.sendmessage_path}"
            response = requests.request("GET", url, params=querystring)

            if self.debug:
                print(response.json())

            if response.status_code == 200:
                print('SendMessage is successed')

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='debug test')
    parser.add_argument('--token')
    parser.add_argument('--msg')
    parser.add_argument('--id')
    parser.add_argument('--getids', type=bool, default=False)
    parser.add_argument('--debug', type=bool, default=False)

    args = parser.parse_args()
    api = TelegramBotApi(args.token, debug=args.debug)

    if args.getids:
        print(api.GetChatIdList())
    elif args.id is not None:
        api.SendMessageId(args.id, args.msg)
    else:
        api.SendMessage(args.msg)