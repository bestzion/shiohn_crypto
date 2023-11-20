import os
import websocket
import json
from datetime import datetime
import threading
from binance.client import Client
from binance.enums import *

# Binance API configuration
api_key = os.environ.get('4w6MMEdawdZ4mkrId3jr3ffOVsbC1qxoQxNkFwR410Gk8Thdb6mcMY20dA1H80b4')
api_secret = os.environ.get('Kg9xKqOKgXZ0aU51DaRGGEzIK1z3YLDDLund4F7EmHB24nIQnRthXlYxcbyC9A6M')
client = Client(api_key, api_secret)

# WebSocket Configuration
SOCKET = "wss://fstream.binance.com/ws/lqtyusdt@kline_1m"
VOLUME_THRESHOLD = 70000
TRADE_INTERVAL = 27 * 60  # 27 minutes in seconds
candles = []

def on_open(ws):
    print('Opened connection')

def on_close(ws):
    print('Closed connection')

def on_message(ws, message):
    global candles
    json_message = json.loads(message)
    kline = json_message['k']
    candle = {
        'start_time': kline['t'] / 1000,
        'open': float(kline['o']),
        'close': float(kline['c']),
        'high': float(kline['h']),
        'low': float(kline['l']),
        'volume': float(kline['v']),
        'is_closed': kline['x']
    }

    if candle['is_closed']:
        candles.append(candle)
        if len(candles) > 3:
            candles.pop(0)
        analyze_and_trade()

def analyze_and_trade():
    if len(candles) < 3:
        return

    first_candle = candles[-3]
    second_candle = candles[-2]
    third_candle = candles[-1]

    first_positive = first_candle['close'] > first_candle['open']
    second_positive = second_candle['close'] > second_candle['open']
    third_positive = third_candle['close'] > third_candle['open']

    first_volume_ok = first_candle['volume'] > VOLUME_THRESHOLD
    second_volume_ok = second_candle['volume'] > VOLUME_THRESHOLD
    third_volume_ok = third_candle['volume'] > VOLUME_THRESHOLD

    if first_volume_ok and second_volume_ok:
        if first_positive and second_positive and not (third_positive and third_volume_ok):
            # Enter short position
            print(f"Entering short position at {datetime.fromtimestamp(candles[-1]['start_time'])}")
            enter_trade("short")
            threading.Timer(TRADE_INTERVAL, exit_position, args=("short",)).start()
        elif not first_positive and not second_positive and not (not third_positive and third_volume_ok):
            # Enter long position
            print(f"Entering long position at {datetime.fromtimestamp(candles[-1]['start_time'])}")
            enter_trade("long")
            threading.Timer(TRADE_INTERVAL, exit_position, args=("long",)).start()

def calculate_order_quantity(balance_fraction):
    balance = client.futures_account_balance()
    total_balance = float(balance[0]['balance'])  # Adjust index as needed
    return total_balance * balance_fraction

def enter_trade(position):
    quantity = calculate_order_quantity(0.1)  # 1/10 of total balance
    if quantity <= 0:
        print("Insufficient balance to open a new position.")
        return

    if position == "long":
        order = client.futures_create_order(symbol='LQTYUSDT', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity)
    elif position == "short":
        order = client.futures_create_order(symbol='LQTYUSDT', side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity)

    print(f"Entered {position} position with order: {order}")

def exit_position(position):
    # Logic to exit the position
    # Implement actual trade exit logic here
    print(f"Exiting {position} position at {datetime.now()}")

def on_error(ws, error):
    print(error)

def main():
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
    ws.run_forever(ping_interval=60)

def on_message(ws, message):
    global candles
    json_message = json.loads(message)
    kline = json_message['k']
    candle = {
        'start_time': kline['t'] / 1000,
        'open': float(kline['o']),
        'close': float(kline['c']),
        'high': float(kline['h']),
        'low': float(kline['l']),
        'volume': float(kline['v']),
        'is_closed': kline['x']
    }

    # Print each candle's data
    if candle['is_closed']:
        print(f"Candle: Time={datetime.fromtimestamp(candle['start_time']).strftime('%Y-%m-%d %H:%M:%S')}, Open={candle['open']}, Close={candle['close']}, High={candle['high']}, Low={candle['low']}, Volume={candle['volume']}")
        candles.append(candle)
        if len(candles) > 3:
            candles.pop(0)
        analyze_and_trade()


if __name__ == "__main__":
    main()
