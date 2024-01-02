# 파이썬 바이낸스 트레이딩 봇
# 지난 거래량 3600개를 가져와서 평균을 구함 (1분봉 기준)
# 평규보다 2배 이상 양봉이 2개 나올 경우
# 7분 후 숏 포지션 진입
# 제작 중

import os
import time
import datetime
from threading import Timer, Thread
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
import logging
from backend import app 
import json

# Configure Logging
logging.basicConfig(filename='/home/ubuntu/Trading/Volume_Statistic/bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a new logger for JSON formatted logs
json_logger = logging.getLogger('jsonLogger')
json_logger.setLevel(logging.INFO)

# Create a file handler for the JSON logger
json_handler = logging.FileHandler('/home/ubuntu/Trading/Volume_Statistic/json_bot.log')
json_logger.addHandler(json_handler)


enter_positions = True
open_positions = []
volume_data = pd.DataFrame()
position_count = 0

def run_flask_app():
    app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=True)


# 숏 포지션 진입을 멈출 수 있음 / stop : 포지션 멈춤 / keep : 다시 진입 가능
def listen_for_stop_command():
    global enter_positions
    print("Enter 'stop' to halt or 'keep' to resume entering new positions:")
    while True:
        command = input()
        if command.lower() == 'stop':
            enter_positions = False
            print("Entering Position has been stopped.")
            logging.info("Entering Position has been stopped.")

        elif command.lower() == 'keep':
            enter_positions = True
            print("Resumed entering positions.")
            logging.info("Resumed entering positions.")

# 유사시 기능, 마진 데이터 불러오기
def get_margin_info(client):
    margin_info = client.futures_account_balance()
    total_margin = 0
    for entry in margin_info:
        if entry['asset'] == 'USDT':
            total_margin = float(entry['balance'])
            break
    return total_margin

# 최근 거래 데이터를 불러옴
def fetch_latest_candles(client, symbol, interval, limit):
    candles = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(candles, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'])
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
    return df

# volume 한계를 걸음
def initialize_volume_threshold(client, symbol, interval):
    global volume_data
    volume_data = pd.DataFrame()

    max_candles_per_request = 1000  # Maximum allowed by Binance API in one request
    candles_needed = 3600

    while candles_needed > 0:
        candles_to_fetch = min(max_candles_per_request, candles_needed)
        new_data = fetch_latest_candles(client, symbol, interval, candles_to_fetch)
        volume_data = pd.concat([new_data[['Volume']], volume_data], ignore_index=True)
        candles_needed -= candles_to_fetch

    return volume_data['Volume'].mean()



def logic(client, symbol, interval, initial_avg_volume):
    global enter_positions, volume_data
    current_avg_volume = initial_avg_volume

    position_entry_timer = None

    def delayed_position_entry():
        global open_positions
        if enter_positions:
            delay_enter_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{delay_enter_time} - Delayed conditions met. Entering short position.")
            logging.info(f"{delay_enter_time} - Delayed conditions met. Entering short position.")
            position = enter_short_position(client, symbol)
            if position:
                open_positions.append(position)

    while True:
        # Fetch the current price
        current_price_info = client.get_symbol_ticker(symbol=symbol)
        current_price = float(current_price_info['price'])

        # Fetch the latest 3 candles for trading logic
        df = fetch_latest_candles(client, symbol, interval, 3)
        new_volume = df['Volume'].iloc[-2]

        # Create a DataFrame for the new volume
        new_volume_df = pd.DataFrame([new_volume], columns=['Volume'])

        # Update the volume data and calculate the new average
        volume_data = pd.concat([volume_data, new_volume_df], ignore_index=True).tail(3600)
        current_avg_volume = volume_data['Volume'].mean()
        volume_threshold = current_avg_volume * 2

        # Check if the last two candles are positive and exceed the current average volume
        candle_1_positive = df['Close'].iloc[-3] > df['Open'].iloc[-3]
        candle_2_positive = df['Close'].iloc[-2] > df['Open'].iloc[-2]
        candle_1_volume = df['Volume'].iloc[-3]
        candle_2_volume = df['Volume'].iloc[-2]

        if enter_positions and candle_1_positive and candle_1_volume > volume_threshold and \
           candle_2_positive and candle_2_volume > volume_threshold:
            if position_entry_timer is None or not position_entry_timer.is_alive():
                print("Conditions met. Preparing to enter short position after delay.")
                logging.info("Conditions met. Preparing to enter short position after delay.")
                position_entry_timer = Timer(7 * 60, delayed_position_entry)
                position_entry_timer.start()
        else:
            if not enter_positions:
                print("Entering positions is currently paused.")
                logging.info("Entering positions is currently paused.")
            else:
                print(f"Conditions not met. Current Avg Volume: {current_avg_volume:.2f}," \
                      f" Current Price: {current_price}, Last First Volume: {candle_2_volume}, Last Second Volume: {candle_1_volume}")
                logging.info(f"Conditions not met. Current Avg Volume: {current_avg_volume:.2f}, Current Price: {current_price}, Last First Volume: {candle_2_volume}, Last Second Volume: {candle_1_volume}")

        check_and_close_positions(client)

        time.sleep(60)


# 숏 포지션 진입
def enter_short_position(client, symbol):
    try:
        enter_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Get current price of LQTY
        price_info = client.futures_mark_price(symbol=symbol)
        current_price = float(price_info['markPrice'])

        # Order Fixed amount. Now 10USDT
        fixed_amount = 50
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
            'entry_price': current_price,
            'order_id': order['orderId']  # Track the order ID
        }
        open_positions.append(position)

        enter_log = {
            'time': enter_time,
            'symbol': 'LQTYUSDT',
            'position': 'Open',
            'price': current_price,
            'profit': 'N/A'
        }
        json_logger.info(json.dumps(enter_log))

        print(f'Entering Short Position has been completed. Time: {enter_time} Entered Price: {current_price}')
        logging.info(f'Entering Short Position has been completed. Time: {enter_time} Entered Price: {current_price}')

        return order
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
        return None

# 지정된 시간이 지났는지 체크
def check_and_close_positions(client):
    current_time = datetime.datetime.now()

    for position in open_positions:
        for position in open_positions:
        # Ensure the 'open_time' key exists for each position
            if 'open_time' in position:
                time_open = current_time - position['open_time']
                if time_open.total_seconds() >= 55 * 60:  # 55 minutes in seconds
                    close_short_position(client, position)


# 숏 포지션 종료 -> Long 주문
def close_short_position(client, position):
    try:
        close_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Fetch the current (exit) price
        price_info = client.futures_mark_price(symbol=position['symbol'])
        exit_price = float(price_info['markPrice'])

        # Calculate profit
        if 'entry_price' in position:
            profit = (position['entry_price'] - exit_price) / position['entry_price']
            profit_percentage = profit * 100
        else:
            profit_percentage = 0  # Default value if entry price is not found

        # Logic to close the short position
        order = client.futures_create_order(
            symbol=position['symbol'],
            side='BUY',  # 'BUY' to close a short position
            type='MARKET',
            quantity=position['quantity'],
            positionSide='SHORT'  # Specify that this is a closing order for a short position
        )

        # Remove the closed position from open_positions
        open_positions.remove(position)

        exit_log = {
            'time': close_time,
            'position': 'Close',
            'symbol': 'LQTYUSDT',
            'price': exit_price,
            'profit': f"{profit_percentage:.2f}%"
        }
        json_logger.info(json.dumps(exit_log))


        print(f"{close_time} - Closed position Price: {exit_price} / Profit: {profit_percentage:.2f}% / ID : {position['order_id']}")
        logging.info(f"{close_time} - Closed position Price: {exit_price} / Profit: {profit_percentage:.2f}% / ID : {position['order_id']}")
    except Exception as e:
        print(f"Error closing position {position['order_id']}: {e}")
        logging.error(f"Error closing position {position['order_id']}: {e}")

# 시작
def main():
    # Start the Flask app in a separate thread
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()

    load_dotenv()
    api_key = os.getenv('api_key')
    api_secret = os.getenv('api_secret')
    client = Client(api_key, api_secret)

    symbol = 'LQTYUSDT'
    interval = Client.KLINE_INTERVAL_1MINUTE

    # Initialize volume threshold
    current_avg_volume = initialize_volume_threshold(client, symbol, interval)
    print(f"Volume Threshold is ready. Begin to operate the bot. Current Avg Volume: {current_avg_volume}")
    logging.info(f"Volume Threshold is ready. Begin to operate the bot. Current Avg Volume: {current_avg_volume}")

    # Start the listener thread
    listener_thread = Thread(target=listen_for_stop_command)
    listener_thread.start()

    # Start the trading logic
    logic(client, symbol, interval, current_avg_volume)

if __name__ == "__main__":
    main()