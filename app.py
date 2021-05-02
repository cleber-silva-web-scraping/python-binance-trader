import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from datetime import date
from binance.enums import *
import repository
from messenger import Messenger 


SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
ORDER_TYPE_MARKET = 'MARKET'
RSI_PERIOD = 14
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
def make_historical():
    global closes
    print("Building Historical")
    historical = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "15 Apr, 2021", DATE_NOW) 
    for h in historical:
        closes.append(h[4])
    
make_historical()

def _order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print("Sending order...")
        order = client.create_order(symbol="ETHBRL", side=side, type=order_type, quantity=quantity)
        repository.orders.insert_one(order)
        messenger.send("{}: {}".format(side, get_info()))
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

def order(side):    
    quantity = TRADE_QUANTITY
    return _order(side, quantity, TRADE_SYMBOL, ORDER_TYPE_MARKET)

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, in_position
    
    #print('received message')
    json_message = json.loads(message)
    #pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))

            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Overbought! Sell! Sell! Sell!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")
            
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY)
                    if order_succeeded:
                        in_position = True                    

                
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
