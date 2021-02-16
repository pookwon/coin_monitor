# 분 켄들 조회
import requests
import json
import datetime
import math
import numpy as np
import threading
from telegram_api import TelegramBotApi
import argparse

# ripple, eos, wax
target_markget = ["KRW-XRP", "KRW-EOS", "KRW-WAXP"]
duration = 7
volume_factor = 3
alert_factor = { "KRW-XRP":7.0, "KRW-EOS":2.0, "KRW-WAXP":3.0 }
check_interval = 60
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
    global duration
    global volume_factor
    global alert_factor

    for market in target_markget:
        mins_datas = GetMinutesData(market, duration)
        cur_time, cur_price = GetCurrentPrice(market)

        if debug:
            #print(f'{cur_time.strftime("%H:%M:%S")} {market}={cur_price}')
            print(mins_datas)

        api = TelegramBotApi(token)
        prev_volume = 0
        for item in mins_datas:
            if prev_volume == 0:
                prev_volume = item["candle_acc_trade_volume"]
                continue

            item_time = datetime.datetime.fromtimestamp(item["timestamp"]/1000)
            diff_time = cur_time - item_time
            
            trade_price = item["trade_price"]
            gap = cur_price - trade_price
            percent = gap / trade_price

            volume = item["candle_acc_trade_volume"]
            gap_volume_multiple = volume / prev_volume
            diff_score = (gap if gap > 0.0 else 0.1) + (gap_volume_multiple / volume_factor)

            # update volume
            prev_volume = item["candle_acc_trade_volume"]

            if diff_score > alert_factor[market]:

                # check last alert time
                last_alert_time = last_alert_market[market]
                interval = datetime.datetime.now() - last_alert_time
                if (interval.total_seconds() / 60) > alert_min_interval:
                    name = GetMarketName(market)
                    desc = "🚀" if gap > 0 else "😭"

                    # alert
                    message = f'{name} {desc} [{cur_time:%H:%M}] {trade_price:1.0f}원 -> {cur_price:1.0f}원 {gap:1.0f}원 {percent * 100:0.2f}%'
                    if market == 'KRW-WAXP':
                        message = f'{name} {desc} [{cur_time:%H:%M}] {trade_price}원 -> {cur_price}원 {gap}원 {percent * 100:0.2f}%'

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
