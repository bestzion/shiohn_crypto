import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from datetime import datetime
import time
import threading

# key, scret key를 .env에서 불러오기
load_dotenv()
key = os.getenv('api_key')
secret = os.getenv('api_secret')

# Binance Futures Client 시작
um_futures_client = UMFutures(key=key, secret=secret)

def start(MM_Deposit, Token_Symbol, historical_usd):
    MM_Deposit = MM_Deposit
    Token_Symbol = Token_Symbol
    historical_usd = historical_usd

# 후보 MM Deposit, Symbol 이름 설정
deposit = ['MM Deposit 4','MM Deposit 5','MM Deposit 11','MM Deposit 15']
Token_Symbol += 'USDT'

# 현재 선물 주문 금액
def get_margin_balance_for_order():
    try:
        account_info = um_futures_client.account(recvWindow=6000)
        margin_balance = float(account_info['marginBalance'])  # Margin balance of the account
        order_amount = margin_balance / 10  # 1/10th of the margin balance
        return order_amount
    except ClientError as e:
        print(f"Error retrieving account information: {e}")
        return 0

# 레버리지 1, Isolated 설정
def market_setting(Token_Symbol):
    leverage_response = um_futures_client.change_leverage(
        symbol=Token_Symbol , leverage=1, recvWindow=6000
    )
    margin_response = um_futures_client.change_margin_type(
        symbol=Token_Symbol, marginType='ISOLATED', recvWindow=6000
    )




# logic 함수 설정
def logic(MM_Deposit, Token_Symbol):
    if MM_Deposit in deposit:
        print(f"Entering short position at {datetime.fromtimestamp(int(candles[-1][0]/1000))}")
        enter_short_position(Token_Symbol)
        timer = threading.Timer(27 * 60, exit_long_position, [Token_Symbol])
        timer.start()


# short 포지션 진입
def enter_short_position(Token_Symbol):
    position_size_usdt = get_margin_balance_for_order()  # Get 1/10th of the margin balance

    try:
        # Fetch the latest market price of the symbol
        latest_price_info = um_futures_client.ticker_price(symbol=Token_Symbol)
        latest_price = float(latest_price_info['price'])

        # Calculate the quantity based on the position size and the latest price
        quantity = position_size_usdt / latest_price

        # Place the market order
        response = um_futures_client.new_order(
            symbol=Token_Symbol,
            side='SELL',  # or 'BUY' depending on your strategy
            type='MARKET',
            quantity=quantity,  # Calculated quantity
            timeInForce='GTC'
        )
        print(f"Order response: {response}")
    except ClientError as e:
        print(f"Error placing order: {e}")
