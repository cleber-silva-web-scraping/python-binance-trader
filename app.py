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


SOCKET = "wss://stream.binance.com:9443/ws/ethbrl@kline_1m"
ORDER_TYPE_MARKET = 'MARKET'
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = "ETHBRL"
TRADE_QUANTITY = 0.008
DATE_NOW = date.today().strftime("%d %b, %y")
print(DATE_NOW)
LOG = "ccd.log" 
SWING_PRICE = 0.0
SWING_MARGIN = 3.0


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



def get_price():    
    get_price = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
    return float(get_price['price'])    

def set_last_price(price = get_price()):
    global SWING_PRICE   
    SWING_PRICE = get_price()    



def has_gain():
    if(SWING_PRICE > 0 and in_position):
        actual_price = get_price()   
        percent = (actual_price - SWING_PRICE) / SWING_PRICE * 100
        if (percent >= SWING_MARGIN ):
            msg = "Has gain. \n*** [{} -> {} = {}%] ***".format(SWING_PRICE, actual_price, float("{:.2f}".format(percent)))
            print(msg)
            messenger.send(msg)
            sell()            


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
    messenger.send("BRL: {}. \nETH: {}.".format(inf['BRL'], inf['ETH']))


schedule.every().hour.do(report)

closes = []
def make_historical():
    global closes
    log("Building Historical")
    historical = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "01 May, 2021", DATE_NOW) 
    for h in historical:
        closes.append(float(h[4]))

make_historical()
    
def message_order(_side, order):
    try:
        msg = "{}: quantity: {}, actual price {}, last price {}".format(_side,
            order['executedQty'], 
            order['fills'][0]['price'],            
            SWING_PRICE)
        messenger.send(msg)        
        repository.orders.insert_one(order)        
        report()
        log(order)
    except Exception as e:
        msg = "an exception occured - {}".format(e)
        log(msg)

def _order(_side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        log("Sending order...")
        order = client.create_order(symbol=TRADE_SYMBOL, side=_side, type=order_type, quantity=quantity)
        message_order(_side, order)
    except Exception as e:
        msg = "an exception occured - {}".format(e)
        log(msg)
        messenger.send(msg)
        return False
    return True

def order(side):    
    quantity = TRADE_QUANTITY
    to_remove = 0.0001
    max_try = 20
    while _order(side, quantity, TRADE_SYMBOL, ORDER_TYPE_MARKET) == False and max_try > 0:
        quantity =  float("{:.4f}".format(quantity - to_remove))
        max_try = max_try - 1
    return max_try > 0

   
def sell():
    global in_position    
    if in_position:
        log("SIDE_SELL")        
        order_succeeded = order(SIDE_SELL)
        if order_succeeded:
            in_position = False
            set_last_price(0.0)
    else:
        log("It is overbought, but we don't own any. Nothing to do.")

def buy():
    global in_position    
    if in_position:
        log("It is oversold, but you already own it, nothing to do.")
    else:
        log("SIDE_BUY")        
        order_succeeded = order(SIDE_BUY)
        if order_succeeded:
            in_position = True       
            set_last_price()    

def on_open(ws):
    log('opened connection')

def on_close(ws):
    log('closed connection')

def on_message(ws, message):
    global closes, in_position
    schedule.run_pending()    
    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']    
   
    has_gain()
    if is_candle_closed:
        log("candle closed at {}".format(close))
        closes.append(float(close))        
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            log("the current rsi is {}".format(last_rsi))
            if last_rsi > RSI_OVERBOUGHT:
               sell()            
            if last_rsi < RSI_OVERSOLD:
                buy()         


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
