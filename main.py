from flask import Flask, request, abort, jsonify
from pprint import pprint
import trading
import go

# Flask 앱 설정
app = Flask(__name__)

# 서버를 대기하는 uri, /webhook 을 넣은 웹을 수신
# webhook을 수신하는 함수 -> POST 인지 확인
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        data = request.get_json()

        if not data:
            abort(400, 'No JSON data received')

        # JSON 데이터를 예쁘게 출력
        print("Received JSON Data:")
        # pprint(data)

        # 필요한 데이터 추출
        MM_Deposit = data.get('transfer', {}).get('toAddress', {}).get('userLabel', {}).get('name')
        Token_Symbol = data.get('transfer', {}).get('tokenSymbol')
        historical_usd = data.get('transfer', {}).get('historicalUSD')

        # 모든 필요한 데이터가 존재하는지 확인
        if all([MM_Deposit, Token_Symbol, historical_usd]):
            # 추출된 데이터를 your_script의 process_data 함수에 전달
            go.start(MM_Deposit, Token_Symbol, historical_usd)

            return jsonify(success=True), 200
        else:
            # 필수 데이터가 누락된 경우
            return jsonify({"error": "Required data missing"}), 400

    elif request.method == 'GET':
        # Handle GET request by pretty-printing the received query parameters
        print("Received GET request with the following data:")
        pprint(request.args)
        return jsonify(message="GET request received and data printed"), 200

    else:
        # POST 요청이 아닌 경우
        abort(400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)