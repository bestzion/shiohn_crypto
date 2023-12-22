import os
import time
import datetime
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client

open_positions = []

def get_margin_info(client):
    margin_info = client.futures_account_balance()
    total_margin = 0

    # Assuming your account's primary currency is USDT
    for entry in margin_info:
        if entry['asset'] == 'USDT':
            total_margin = float(entry['balance'])
            break

    return total_margin

def fetch_market_data(client, symbol, interval, current_avg_volume, candle_count):
    df = fetch_latest_candles(client, symbol, interval, 1)
    if not df.empty:
        new_volume = df['Volume'].iloc[-1]
        # Update the volume threshold
        new_avg_volume = ((current_avg_volume * candle_count) + new_volume) / (candle_count + 1)
        return new_avg_volume, candle_count + 1
    return current_avg_volume, candle_count

def fetch_latest_candles(client, symbol, interval, limit):
    # Fetch candles from Binance API
    candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    # Convert to DataFrame
    df = pd.DataFrame(candles, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'])
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
    return df


def logic(client, symbol, current_avg_volume, candle_count):
    total_margin = get_margin_info(client)  # Retrieve total margin

    while True:
        current_avg_volume, candle_count = fetch_market_data(client, symbol, Client.KLINE_INTERVAL_1MINUTE, current_avg_volume, candle_count)

        # Fetch the latest 3 candles
        df = fetch_latest_candles(client, symbol, Client.KLINE_INTERVAL_1MINUTE, 3)

        if len(df) < 3:
            print("Not enough data yet.")
            time.sleep(60)
            continue

        # Check if the last two candles are positive and exceed the current average volume
        candle_1_positive = df['Close'].iloc[-3] > df['Open'].iloc[-3]
        candle_2_positive = df['Close'].iloc[-2] > df['Open'].iloc[-2]
        candle_1_volume = df['Volume'].iloc[-3]
        candle_2_volume = df['Volume'].iloc[-2]

        if candle_1_positive and candle_1_volume > current_avg_volume and \
           candle_2_positive and candle_2_volume > current_avg_volume:
            print("Conditions met. Entering short position.")
            enter_short_position(client, symbol)
        else:
            print(f"Conditions not met. Current Avg Volume: {current_avg_volume}, Candle -2 Volume: {candle_2_volume}, Candle -3 Volume: {candle_1_volume}")

        time.sleep(60)


def enter_short_position(client, symbol):
    try:
        # Get current price of LQTY
        price_info = client.futures_mark_price(symbol=symbol)
        current_price = float(price_info['markPrice'])

        # Order Fixed amount. Now 10USDT
        fixed_amount = 10
        quantity = fixed_amount / current_price 

        # Adjust quantity to a valid scale for LQTY
        quantity = round(quantity, 1)  # Replace with appropriate decimal places

        # Place a futures short order
        order = client.futures_create_order(
            symbol=symbol,
            side='SELL',  # 'SELL' for short
            type='MARKET',  # 'MARKET' type for immediate execution at current price
            quantity=quantity,
            positionSide='SHORT'  # 'SHORT' for short position
        )

        # Record the position with its opening time
        position = {
            'symbol': symbol,
            'quantity': quantity,
            'open_time': datetime.datetime.now(),
            'order_id': order['orderId']  # Track the order ID
        }
        open_positions.append(position)

        return order
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def check_and_close_positions(client):
    current_time = datetime.datetime.now()
    positions_to_close = []

    for position in open_positions:
        time_open = current_time - position['open_time']
        if time_open.total_seconds() >= 55 * 60:  # 55 minutes in seconds
            positions_to_close.append(position)

    for position in positions_to_close:
        close_short_position(client, position)
        open_positions.remove(position)

def close_short_position(client, position):
    try:
        # Logic to close the short position
        order = client.futures_create_order(
            symbol=position['symbol'],
            side='BUY',  # 'BUY' to close a short position
            type='MARKET',
            quantity=position['quantity'],
            positionSide='SHORT'  # Specify that this is a closing order for a short position
        )
        print(f"Closed position: {position['order_id']}")
    except Exception as e:
        print(f"Error closing position {position['order_id']}: {e}")

def main():
    # 키 정보를 env에서 가져오기
    load_dotenv()
    api_key = os.getenv('api_key')
    api_secret = os.getenv('api_secret')
    client = Client(api_key, api_secret)

    # Define the trading symbol and other parameters
    symbol = 'LQTYUSDT'
    interval = Client.KLINE_INTERVAL_1MINUTE
    initial_avg_volume = 6211
    candle_count = 60

    print("Initial Volume threshold is ready, start to make position")
    logic(client, symbol, initial_avg_volume, candle_count)

if __name__ == "__main__":
    main()