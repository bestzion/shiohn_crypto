from flask import Flask, jsonify, render_template, request  # Include 'request' here
import json


app = Flask(__name__)

def get_last_25_log_lines():
    try:
        with open('/home/ubuntu/Trading/Volume_Statistic/bot.log', 'r') as file:
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
        # Implement logic to calculate total profit
        total_profit = 0  # Replace with actual calculation

        log_content = get_last_25_log_lines()

        response_data = {'total_profit': total_profit, 'log_content': log_content}

        return jsonify(response_data)
    except Exception as e:
        print(f"Error in bot_output: {e}")
        # Send an error message to the frontend
        return jsonify({'error': 'An error occurred fetching data'})


def get_paginated_trading_data(page, per_page):
    try:
        with open('/home/ubuntu/Trading/Volume_Statistic/json_bot.log', 'r') as file:
            log_entries = [json.loads(line.strip()) for line in file.readlines()]
            start = (page - 1) * per_page
            end = start + per_page
            return log_entries[start:end]
    except Exception as e:
        print(f"Error reading JSON trading log file: {e}")
        return []
        return []

@app.route('/json-data')
def json_data():
    try:
        log_entries = []
        with open('/home/ubuntu/Trading/Volume_Statistic/json_bot.log', 'r') as file:
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')