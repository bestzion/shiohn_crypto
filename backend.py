from flask import Flask, jsonify, render_template
import json

app = Flask(__name__)

def get_last_25_log_lines():
    try:
        with open('/Users/zion/Library/Mobile Documents/com~apple~CloudDocs/Shi-Ohn/Coding/Trading/AWS/bot.log', 'r') as file:
            log_lines = file.readlines()

            # Filter out Flask HTTP request log lines
            filtered_lines = [line for line in log_lines if not "GET /" in line and not "POST /" in line]

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
    return render_template('index.html')

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


@app.route('/json-data')
def json_data():
    try:
        with open('/Users/zion/Library/Mobile Documents/com~apple~CloudDocs/Shi-Ohn/Coding/Trading/AWS/json_bot.log', 'r') as file:
            json_data = json.load(file)
            return jsonify(json_data)
    except Exception as e:
        print(f"Error reading JSON log file: {e}")
        return jsonify({'error': 'An error occurred fetching JSON data'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)