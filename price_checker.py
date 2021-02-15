# 분 켄들 조회
import requests
import json
import datetime
import math
import numpy as np
import threading
from telegram_api import TelegramBotApi
import argparse

# ripple
target_markget = ["KRW-XRP", "KRW-EOS"]
condition = {"duration":10, "gap":0.01}
check_interval = 30
alert_min_interval = 20
token = ''
debug = False
market_names = None
last_alert_market = {}

def GetMarketName(name):
    global market_names
    if market_names is None:
        url = "https://api.upbit.com/v1/market/all"
        querystring = {"isDetails":"false"}
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            market_names = response.json()
    
    if market_names is not None:
        for item in market_names:
            if item["market"] == name:
                return item["korean_name"]

    return None


def GetMinutesData(market, count=20):
    url = "https://api.upbit.com/v1/candles/minutes/1"
    #querystring = {"market":"KRW-XRP","to":"2021-02-05T00:00:00Z", "count": str(get_count)}
    querystring = {"market":market,"count":count}
    response = requests.request("GET", url, params=querystring)
    if response.status_code == 200:
        return response.json()
    
    #print(response.text)

    return None

def GetCurrentPrice(market):
    url = "https://api.upbit.com/v1/ticker"
    querystring = {"markets":market}
    response = requests.request("GET", url, params=querystring)
    if response.status_code != 200:
        return None, None

    result = response.json()

    #print(json.dumps(result))
    #print(result[0]["trade_price"], result[0]["change"])
    cur_time = datetime.datetime.fromtimestamp(result[0]["timestamp"]/1000)

    return cur_time, result[0]["trade_price"]

def priceCheck():
    global last_alert_market
    global alert_min_interval
    global token
    global debug
    global condition

    for market in target_markget:
        mins_datas = GetMinutesData(market, condition["duration"])
        cur_time, cur_price = GetCurrentPrice(market)

        if debug:
            #print(f'{cur_time.strftime("%H:%M:%S")} {market}={cur_price}')
            print(mins_datas)

        api = TelegramBotApi(token)

        for item in mins_datas:
            item_time = datetime.datetime.fromtimestamp(item["timestamp"]/1000)
            diff_time = cur_time - item_time
            if diff_time.total_seconds() < 59:
                continue

            trade_price = item["trade_price"]
            diff_price = cur_price - trade_price

            percent = math.fabs(diff_price) / trade_price

            if percent > condition["gap"]:
                # check last alert time
                last_alert_time = last_alert_market[market]
                interval = datetime.datetime.now() - last_alert_time
                if (interval.total_seconds() / 60) > alert_min_interval:
                    name = GetMarketName(market)
                    desc = "🚀" if diff_price > 0 else "😭"

                    # alert
                    message = f'{name} {desc} [{cur_time:%H:%M}] {trade_price}원 -> {cur_price}원 {diff_price:0}원 {percent * 100:0.2f}%'
                    if debug == False:
                        api.SendMessage(message)

                    if debug:
                        print(message)

                    last_alert_market[market] = datetime.datetime.now()
                break
            
            if debug:
                print(market, item["candle_date_time_kst"], cur_time.strftime("%m/%d %H:%M:%S"), item["trade_price"], item["candle_acc_trade_volume"])

        #print(price_volumes)

def priceCheckTimer():
    priceCheck()
    timer = threading.Timer(check_interval, priceCheckTimer)
    timer.start()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='debug test')
    parser.add_argument('--token', type=str)
    parser.add_argument('--debug', type=bool, default=False)

    args = parser.parse_args()

    # start
    token = args.token
    debug = args.debug

    for market in target_markget:
        last_alert_market[market] = datetime.datetime.now()

    priceCheckTimer()
