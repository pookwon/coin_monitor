# 분 켄들 조회
import requests
import json
import datetime
import time
import math
import numpy as np
import threading
from telegram_api import TelegramBotApi
import argparse

# ripple, eos, wax
#target_markget = ["KRW-XRP", "KRW-EOS", "KRW-WAXP"]
target_markget = ["KRW-XRP", "KRW-EOS", "KRW-BTC", "KRW-BORA"]
duration = 60
check_duration = 6
volume_factor = 5
alert_factor = { "KRW-XRP":4.5, "KRW-EOS":4.5, "KRW-BTC":3.5, "KRW-BORA":5}
check_interval = 60
alert_min_interval = 30

token = ''
line_token = None
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

def NotifyToLine(message, token):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + token}
    datas = {'message': message }
    response = requests.post(url, headers=headers, data=datas)
    if response.status_code == 200:
        return True
    return False

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
    global line_token
    global debug
    global duration
    global volume_factor
    global alert_factor
    
    for market in target_markget:

        # check last alert time
        last_alert_time = last_alert_market[market]
        interval = datetime.datetime.now() - last_alert_time

        if (interval.total_seconds() / 60) < alert_min_interval:
            continue

        time.sleep(5)

        mins_datas = GetMinutesData(market, duration)
        cur_time, cur_price = GetCurrentPrice(market)

        #if debug:
            #print(f'{cur_time.strftime("%H:%M:%S")} {market}={cur_price}')
        #    print(mins_datas)

        api = TelegramBotApi(token)

        # get volume avg
        volumes = []
        for item in mins_datas:
            volumes.append(item["candle_acc_trade_volume"])
        volume_avg = np.average(np.array(volumes))

        index = -1
        for item in mins_datas:
            index += 1

            if check_duration < index:
                break

            item_time = datetime.datetime.fromtimestamp(item["timestamp"]/1000)
            diff_time = cur_time - item_time
            
            trade_price = item["trade_price"]
            gap = cur_price - trade_price
            percent = gap / trade_price * 100

            volume = item["candle_acc_trade_volume"]
            gap_volume_multiple = volume / volume_avg
            diff_score = (math.fabs(percent) * 5) + (gap_volume_multiple / volume_factor)

            if debug:
                print(f'{item["candle_date_time_kst"]} gap:{gap:1.2f}, price:{item["trade_price"]:1.2f}, {percent:0.1f}%, {gap:1.2f}, {gap_volume_multiple:0.2f}, {diff_score:0.2f}')

            # update volume
            prev_volume = item["candle_acc_trade_volume"]

            if gap == 0.0:
                continue

            if diff_score > alert_factor[market]:
                name = GetMarketName(market)
                desc = "🚀" if gap > 0 else "😭"

                # get prev 5
                price_before5min = mins_datas[index + 5]["trade_price"]

                # alert
                if market == "KRW-BTT":
                    message = f'{name} {desc} [{cur_time:%H:%M}] 5분전:{price_before5min:0.2f}원, {trade_price:0.2f}원 -> {cur_price:0.2f}원 {gap:0.2f}원 {percent:0.2f}%'
                else:
                    message = f'{name} {desc} [{cur_time:%H:%M}] 5분전:{int(price_before5min):,}원, {int(trade_price):,}원 -> {int(cur_price):,}원 {int(gap):,}원 {percent:0.2f}%'

                if debug == False:
                    api.SendMessage(message)

                if debug:
                    print(message)

                if line_token is not None:
                    NotifyToLine(message, line_token)

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
    parser.add_argument('--line_token', type=str, default=None)
    parser.add_argument('--debug', type=bool, default=False)

    args = parser.parse_args()

    # start
    token = args.token
    line_token = args.line_token
    debug = args.debug

    for market in target_markget:
        last_alert_market[market] = datetime.datetime.now() - datetime.timedelta(minutes=30)

    priceCheckTimer()
