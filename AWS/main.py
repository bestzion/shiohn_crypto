# import logging
# import json
# import os
# from dotenv import load_dotenv
# from binance.client import Client  # Import the Binance Client
# from binance_order import start  # Import the start function
# from flask import Flask, request, abort, jsonify

# # Flask 앱 설정
# app = Flask(__name__)

# # Initialize Binance Client
# load_dotenv()
# api_key = os.getenv('api_key')
# api_secret = os.getenv('api_secret')
# client = Client(api_key, api_secret)

# # Configure logging
# logging.basicConfig(filename='/home/ubuntu/Trading/Upbit/arkham.log', level=logging.INFO, format='%(asctime)s %(message)s')

# # 서버를 대기하는 uri, /webhook 을 넣은 웹을 수신
# # webhook을 수신하는 함수 -> POST 인지 확인
# @app.route('/webhook', methods=['POST', 'GET'])
# def webhook():
#     if request.method == 'POST':
#         data = request.get_json()

#         if not data:
#             abort(400, 'No JSON data received')

#         # 필요한 데이터 추출
#         MM_Deposit = data.get('transfer', {}).get('toAddress', {}).get('userLabel', {}).get('name')
#         Token_Symbol = data.get('transfer', {}).get('tokenSymbol')
#         historical_usd = data.get('transfer', {}).get('historicalUSD')
#         Block_Time = data.get('transfer', {}).get('blockTimestamp')  # Extracting blockTimestamp


#         # 모든 필요한 데이터가 존재하는지 확인
#         if all([MM_Deposit, Token_Symbol, historical_usd, Block_Time]):

#             # Log the received data
#             arkham_log = {
#                 'MM_Deposit': MM_Deposit,
#                 'Token_Symbol': Token_Symbol,
#                 'historical_usd': historical_usd,
#                 'Block Time': block_time
#             }
#             logging.info(json.dumps({arkham_log}))

#             # Check if any required data is missing
#             missing_fields = [field for field in ["MM_Deposit", "Token_Symbol", "historical_usd", "Block_Time"] if locals()[field] is None]
#             if missing_fields:
#                 return jsonify({"error": "Required data missing", "missing_fields": missing_fields}), 400

            
#             # Call the start function from binance_order.py
#             # Pass the extracted data to the start function
#             start(client, MM_Deposit, Token_Symbol, historical_usd)

#             print(f"Block Time: {Block_Time} | MM_Deposit: {MM_Deposit} | Token: {Token_Symbol}")
#             return jsonify(success=True), 200
        
#         else:
#             # 필수 데이터가 누락된 경우
#             return jsonify({"error": "Required data missing"}), 400

#     elif request.method == 'GET':
#         # Handle GET request by pretty-printing the received query parameters
#         print("Received GET request with the following data:")
#         return jsonify(message="GET request received and data printed"), 200

#     else:
#         # POST 요청이 아닌 경우
#         abort(400)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, use_reloader=False, debug=True)

import logging
import json
import os
from dotenv import load_dotenv
from binance.client import Client  # Import the Binance Client
from binance_order import start  # Import the start function
from flask import Flask, request, abort, jsonify

# Flask 앱 설정
app = Flask(__name__)

# Initialize Binance Client
load_dotenv()
api_key = os.getenv('api_key')
api_secret = os.getenv('api_secret')
client = Client(api_key, api_secret)

# Configure logging
logging.basicConfig(filename='/home/ubuntu/Trading/Upbit/arkham.log', level=logging.INFO, format='%(asctime)s %(message)s')

# 서버를 대기하는 uri, /webhook 을 넣은 웹을 수신
# webhook을 수신하는 함수 -> POST 인지 확인
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        data = request.get_json()

        # Log the entire request data for debugging
        print("Received GET request data:", data)

        if not data:
            abort(400, 'No JSON data received')

        # [Your existing code for processing the data]

    elif request.method == 'POST':
        data = request.get_json()

        if not data:
            abort(400, 'No JSON data received')

        # Extract MM_Deposit assuming it's the 'name' under 'arkhamEntity' in 'toAddress'
        MM_Deposit = data.get('transfer', {}).get('toAddress', {}).get('arkhamEntity', {}).get('name')
        Token_Symbol = data.get('transfer', {}).get('tokenSymbol')
        historical_usd = data.get('transfer', {}).get('historicalUSD')
        Block_Time = data.get('transfer', {}).get('blockTimestamp')

        # Log the received data
        arkham_log = {
            'MM_Deposit': MM_Deposit,
            'Token_Symbol': Token_Symbol,
            'historical_usd': historical_usd,
            'Block Time': Block_Time
        }
        logging.info(json.dumps(arkham_log))

        # Call the start function from binance_order.py
        # Pass the extracted data to the start function
        # start(client, MM_Deposit, Token_Symbol, historical_usd)
        print(f"Block Time: {Block_Time} | MM_Deposit: {MM_Deposit} | Token: {Token_Symbol}")

        # Additional processing can be done here as needed
        return jsonify({"MM_Deposit": MM_Deposit, "Token_Symbol": Token_Symbol})


    else:
        abort(400)

    return jsonify({"message": "Request processed successfully"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)