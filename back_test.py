import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from datetime import date, datetime


from binance.enums import *
import repository
from messenger import Messenger 


SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
ORDER_TYPE_MARKET = 'MARKET'
RSI_PERIOD = 21
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = "ETHBRL"
TRADE_QUANTITY = 0.009
DATE_NOW = date.today().strftime("%d %b, %y")
in_position = False

client = Client(config.API_KEY, config.API_SECRET)
messenger = Messenger()


def get_info():
    info = client.get_account()
    retorno = ""
    for inf in info['balances']:
        if(inf['asset'] == "BRL" or inf['asset'] == "ETH"):
            retorno = "{} {}: {}.".format(retorno, inf['asset'], inf['free'])

    return retorno.strip()



closes = []
historical = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "28 Apr, 2021", "01 May, 2021") 

     
for h in historical: 
    h[0] = datetime.fromtimestamp(h[0]/ 1000).strftime("%d-%m-%Y %H:%M:%S")
    closes.append(float(h[4]))
    if len(closes) > RSI_PERIOD:
        np_closes = numpy.array(closes)
        
        rsi = talib.RSI(np_closes, RSI_PERIOD)


        last_rsi = rsi[-1]
        #print("the current rsi is {}".format(last_rsi))

        if last_rsi > RSI_OVERBOUGHT:
            if in_position:
                print("Sell! Sell! Sell!")      
                print(h)    
                print(last_rsi)        
                print('-----------------------')                
                in_position = False           
        
        if last_rsi < RSI_OVERSOLD:
            if not in_position:                
                print("Buy! Buy! Buy!")
                print(h)            
                print(last_rsi)        
                print('-----------------------')
                in_position = True
                                

                
