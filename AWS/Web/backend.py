from flask import Flask, jsonify, render_template, request  # Include 'request' here
import json


app = Flask(__name__)


def calculate_total_profit():
    total_profit = 0.0

    try:
        with open('/home/ubuntu/Trading/Volume/json_bot.log', 'r') as file:
            for line in file:
                data = json.loads(line)
                profit_str = data.get('profit')
                if profit_str and profit_str != 'N/A':
                    # Remove '%' and convert to float. This handles negative numbers as well.
                    profit_percent = float(profit_str.strip('%'))
                    total_profit += profit_percent
    except Exception as e:
        print(f"Error reading json_bot.log: {e}")

    return total_profit


def get_paginated_trading_data(page, per_page):
    try:
        with open('/home/ubuntu/Trading/Volume/json_bot.log', 'r') as file:
            log_entries = [json.loads(line.strip()) for line in file.readlines()]
            start = (page - 1) * per_page
            end = start + per_page
            return log_entries[start:end]
    except Exception as e:
        print(f"Error reading JSON trading log file: {e}")
        return []


def calculate_win_ratio():
    win_count = 0
    total_count = 0

    with open('/home/ubuntu/Trading/Volume/json_bot.log', 'r') as file:
        for line in file:
            data = json.loads(line)
            if data["position"] == "Close" and data["profit"] != "N/A":
                total_count += 1
                profit = float(data["profit"].strip('%'))
                if profit > 0:
                    win_count += 1

    win_ratio = (win_count / total_count) * 100 if total_count > 0 else 0
    return win_ratio


def get_last_25_log_lines():
    try:
        with open('/home/ubuntu/Trading/Volume/bot.log', 'r') as file:
            log_lines = file.readlines()

            # Filter out Flask HTTP request log lines
            filtered_lines = [line for line in log_lines if not "BAD_REQUEST" in line and not "HTTP" in line and not "GET /" in line and not "POST /" in line and "ERROR" not in line]

            # Get the last 25 lines after filtering
            last_25_lines = filtered_lines[-25:]

            # Extract the message part from each line
            extracted_messages = [line.split(' - ')[-1].strip() for line in last_25_lines]
            return extracted_messages
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of entries per page
    trading_data = get_paginated_trading_data(page, per_page)
    return render_template('index.html', trading_data=trading_data, current_page=page)


@app.route('/bot-output')
def bot_output():
    try:
        total_profit = calculate_total_profit()
        win_ratio = calculate_win_ratio()
        log_content = get_last_25_log_lines()  # Assuming this function is already defined

        response_data = {'total_profit': total_profit, 'win_ratio': win_ratio, 'log_content': log_content}
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in bot_output: {e}")
        return jsonify({'error': 'An error occurred fetching data'})


@app.route('/json-data')
def json_data():
    try:
        log_entries = []
        with open('/home/ubuntu/Trading/Volume/json_bot.log', 'r') as file:
            for line in file:
                try:
                    log_entry = json.loads(line)
                    log_entries.append(log_entry)
                except json.JSONDecodeError:
                    continue  # Ignore lines that are not valid JSON
        return jsonify(log_entries)
    except Exception as e:
        print(f"Error reading JSON log file: {e}")
        return jsonify({'error': 'An error occurred fetching JSON data'})





def parse_log_line(line):
    # 로그 라인을 파싱해서 필요한 정보를 추출하는 함수를 구현해야 합니다.
    # 이는 'trading.log' 파일의 실제 포맷에 맞춰서 조정되어야 합니다.
    # 예시 코드입니다.
    data = json.loads(line)
    return {
        'time': data.get('time', ''),
        'symbol': data.get('symbol', ''),
        'side': data.get('side', ''),
        'position': data.get('position', ''),
        'price': data.get('price', ''),
        'MM Deposit': data.get('MM Deposit', ''),
        'profit': data.get('profit', '')
    }


@app.route('/arkham-log')
def arkham_log():
    try:
        with open('/home/ubuntu/Trading/Upbit/arkham.log', 'r') as file:
            content = file.readlines()  # 파일의 모든 라인을 읽습니다.
        return render_template('/home/ubuntu/Trading/Web/templates/MM.html', lines=content)  # 'arkham.html' 템플릿과 로그 라인들을 렌더링합니다.
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # 에러 발생 시 에러 메시지와 함께 500 상태 코드 반환


@app.route('/MM-trading-data')
def mm_trading_data():
    try:
        with open('/home/ubuntu/Trading/Upbit/trading.log', 'r') as file:
            lines = file.readlines()
            # 로그 파일을 파싱해서 JSON 형태로 변환하는 로직을 구현합니다.
            data = [parse_log_line(line) for line in lines if line.strip()]  # 빈 줄은 제외하고 파싱
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=True)

# , ssl_context='adhoc'
