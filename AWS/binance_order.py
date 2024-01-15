import time
import datetime
from threading import Timer
from binance.client import Client
import logging
import json

open_short_positions = []
open_long_positions = []

# Configure logging
logging.basicConfig(filename='trading.log', level=logging.INFO, format='%(asctime)s %(message)s')
json_logger = logging.getLogger('json_logger')

# 후보 MM Deposit, Symbol 이름 설정
deposit = ['MM Deposit 5','MM Deposit 11','MM Deposit 15']

# main.py에서 webhook 정보 받을 경우 실행됨
def start(client, MM_Deposit, Token_Symbol, historical_usd):
    if MM_Deposit in deposit:
        symbol = Token_Symbol + 'USDT'

        if MM_Deposit == 'MM Deposit 5':
            # Delay for 1 hour (3600 seconds)
            time.sleep(3600)
            enter_short_position(client, symbol, MM_Deposit)

        elif MM_Deposit == 'MM Deposit 15':
            enter_short_position(client, symbol, MM_Deposit)

        elif MM_Deposit == 'MM Deposit 11':
            enter_long_position(client, symbol, MM_Deposit)


# 숏 포지션 진입
def enter_short_position(client, symbol, MM_Deposit):
    try:
        enter_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Get current price of the symbol
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

        order_id = order['orderID']

        # Record the position with its opening time
        position = {
            'symbol': symbol,
            'quantity': quantity,
            'open_time': datetime.datetime.now(),
            'entry_price': current_price,
            'order_id': order['orderId']  # Track the order ID
        }
        open_short_positions.append(position)

        enter_log = {
            'time': enter_time,
            'symbol': symbol,
            'side' : 'Short',
            'position': 'Open',
            'price': current_price,
            'MM Deposit': MM_Deposit,
            'profit': 'N/A'
        }
        json_logger.info(json.dumps(enter_log))

        if MM_Deposit == 'MM Deposit 5':
            Timer(3 * 3600, exit_short_position, [client, order_id, MM_Deposit]).start()  # 3 hours
        elif MM_Deposit == 'MM Deposit 15':
            Timer(4 * 3600, exit_short_position, [client, order_id, MM_Deposit]).start()  # 4 hours


        print(f'Entering Short Position has been completed. Time: {enter_time}, Symbol: {symbol}, Entered Price: {current_price}, Deposit: {MM_Deposit}')
        logging.info(f'Entering Short Position has been completed. Time: {enter_time}, Symbol: {symbol}, Entered Price: {current_price}, Deposit: {MM_Deposit}')

        return order
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
        return None
    
# 롱 포지션 진입
def enter_long_position(client, symbol, MM_Deposit):
    try:
        enter_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Get current price of the symbol
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
            side='BUY',  # 'SELL' for short
            type='MARKET',  # 'MARKET' type for immediate execution at current price
            quantity=quantity,
            positionSide='LONG'  # 'SHORT' for short position
        )

        order_id = order['orderID']

        # Record the position with its opening time
        position = {
            'symbol': symbol,
            'quantity': quantity,
            'open_time': datetime.datetime.now(),
            'entry_price': current_price,
            'order_id': order['orderId']  # Track the order ID
        }
        open_long_positions.append(position)

        enter_log = {
            'time': enter_time,
            'symbol': symbol,
            'side': 'Short',
            'position': 'Open',
            'price': current_price,
            'MM Deposit': MM_Deposit,
            'profit': 'N/A'
        }
        json_logger.info(json.dumps(enter_log))

        if MM_Deposit == 'MM Deposit 11':
            Timer(1 * 3600, exit_long_position, [client, order_id, MM_Deposit]).start()  # 1 hour

        print(f'Entering Long Position has been completed. Time: {enter_time}, Symbol: {symbol}, Entered Price: {current_price}, Deposit: {MM_Deposit}')
        logging.info(f'Entering Long Position has been completed. Time: {enter_time}, Symbol: {symbol}, Entered Price: {current_price}, Deposit: {MM_Deposit}')

        return order
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
        return None
    

def exit_short_position(client, order_id, MM_Deposit):
    try:
        for position in open_short_positions[:]:
            if position['order_id'] == order_id:
                symbol = position['symbol']
                quantity = position['quantity']

            # Place a futures buy order to exit short position
            order = client.futures_create_order(
                symbol=symbol,
                side='BUY',  # 'BUY' to exit short
                type='MARKET',  # 'MARKET' type for immediate execution
                quantity=quantity,
                positionSide='SHORT'  # 'SHORT' for short position
            )

            # Get current price for the symbol
            price_info = client.futures_mark_price(symbol=symbol)
            current_price = float(price_info['markPrice'])

            # Calculate profit as a percentage
            enter_price = position['entry_price']
            profit_percentage = (enter_price - current_price) / enter_price * 100

            # Record the exit time
            exit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            exit_log = {
                'time': exit_time,
                'symbol': symbol,
                'side': 'Short',
                'position': 'Closed',
                'price': current_price,
                'MM Deposit': MM_Deposit,
                'profit': f"{profit_percentage:.2f}%"
            }
            json_logger.info(json.dumps(exit_log))

            # Optionally, remove the position from the list
            open_short_positions.remove(position)

        return True
    except Exception as e:
        logging.error(f"An error occurred while exiting short position: {e}")
        return False

def exit_long_position(client, order_id, MM_Deposit):
    try:
        for position in open_long_positions[:]:
            if position['order_id'] == order_id:
                symbol = position['symbol']
                quantity = position['quantity']

            # Place a futures buy order to exit short position
            order = client.futures_create_order(
                symbol=symbol,
                side='SELL',  # 'SELL' to exit short
                type='MARKET',  # 'MARKET' type for immediate execution
                quantity=quantity,
                positionSide='LONG'  # 'LONG' for long position
            )

            # Get current price for the symbol
            price_info = client.futures_mark_price(symbol=symbol)
            current_price = float(price_info['markPrice'])

            # Calculate profit as a percentage
            enter_price = position['entry_price']
            profit_percentage = (enter_price - current_price) / enter_price * 100

            # Record the exit time
            exit_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            exit_log = {
                'time': exit_time,
                'symbol': symbol,
                'side': 'Long',
                'position': 'Closed',
                'price': current_price,
                'MM Deposit': MM_Deposit,
                'profit': f"{profit_percentage:.2f}%"
            }
            json_logger.info(json.dumps(exit_log))

            # Optionally, remove the position from the list
            open_long_positions.remove(position)

        return True
    except Exception as e:
        logging.error(f"An error occurred while exiting long position: {e}")
        return False
