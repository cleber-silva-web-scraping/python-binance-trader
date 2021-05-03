import websocket, json, talib, numpy
import config
from binance.client import Client
import time
from datetime import date
from datetime import datetime
from binance.enums import *
import repository
from messenger import Messenger 
import schedule


SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
ORDER_TYPE_MARKET = 'MARKET'
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = "ETHBRL"
TRADE_QUANTITY = 0.008
DATE_NOW = date.today().strftime("%d %b, %y")
LOG = "ccd.log" 
 
SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'

client = Client(config.API_KEY, config.API_SECRET)
messenger = Messenger()



def get_info():
    info = client.get_account()
    retorno = {}
    for inf in info['balances']:
        if(inf['asset'] == "BRL" or inf['asset'] == "ETH"):
            retorno[inf['asset']] = inf['free']

    return retorno



in_position = True
inf = get_info()
if(float(inf['BRL']) > 120):
    in_position = False

def log(message):
    print(message)
    with open(LOG, 'w') as writer: 
             
        data = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        writer.write("[{}] {}".format(data, message))

print("In position: {}".format(in_position))
print('==============================')
print("")


def report():
    inf = get_info()   
    messenger.send("BRL: {}. ETH: {}".format(inf['BRL'], inf['ETH']))


schedule.every().hour.do(report)

closes = []
def make_historical():
    global closes
    log("Building Historical")
    historical = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "15 Apr, 2021", DATE_NOW) 
    for h in historical:
        closes.append(float(h[4]))
    

def _order(_side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        log("Sending order...")
        order = client.create_order(symbol=TRADE_SYMBOL, side=_side, type=order_type, quantity=quantity)
        repository.orders.insert_one(order)
        report()
        log(order)
    except Exception as e:
        log("an exception occured - {}".format(e))
        return False
    return True

def order(side):    
    quantity = TRADE_QUANTITY
    return _order(side, quantity, TRADE_SYMBOL, ORDER_TYPE_MARKET)


def on_open(ws):
    log('opened connection')

def on_close(ws):
    log('closed connection')

def on_message(ws, message):
    global closes, in_position
    schedule.run_pending()
    #log('received message')
    json_message = json.loads(message)
    #plog.plog(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        log("candle closed at {}".format(close))
        closes.append(float(close))

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            log("the current rsi is {}".format(last_rsi))

            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    log("Overbought! Sell! Sell! Sell!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL)
                    if order_succeeded:
                        in_position = False
                else:
                    log("It is overbought, but we don't own any. Nothing to do.")
            
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    log("It is oversold, but you already own it, nothing to do.")
                else:
                    log("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY)
                    if order_succeeded:
                        in_position = True                    

                
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
