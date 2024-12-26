from flask import Flask, render_template, jsonify
import requests
import logging
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = app.logger

NODES = [
    {
        "name": "Pump House 3",
        "coordinates": [17.4435, 78.3489],
        "channel_id": "2611172",
        "api_key": "OEORJPRA3IXMCARG"
    }
]

@app.route('/')
def home():
    return render_template('index.html', nodes=NODES)

@app.route('/api/data/<channel_id>/<api_key>')
def get_data(channel_id, api_key):
    try:
        url = f'https://api.thingspeak.com/channels/{channel_id}/feeds.json'
        params = {
            'api_key': api_key,
            'results': 20,  # Increased number of results for better graph
            'round': 2
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)  # Reduced timeout
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error fetching data from ThingSpeak: {e}")
            return jsonify({"error": "Failed to load data"}), 500

        data = response.json()
        logger.debug(f"ThingSpeak Response: {data}")

        if 'feeds' not in data or not data['feeds']:
            return jsonify({"error": "No data available"}), 404

        processed_data = {
            'timestamps': [],
            'temperature': [],
            'distance': []
        }

        for feed in reversed(data['feeds']):  # Reverse to show newest data first
            try:
                timestamp = datetime.strptime(feed['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                formatted_time = timestamp.strftime('%H:%M')  # Only show time for cleaner x-axis
                
                temperature = None
                if 'field1' in feed and feed['field1'] is not None:
                    try:
                        temperature = round(float(feed['field1']), 1)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid temperature value: {feed['field1']}")

                distance = None
                if 'field2' in feed and feed['field2'] is not None:
                    try:
                        distance = round(float(feed['field2']), 1)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid distance value: {feed['field2']}")

                processed_data['timestamps'].append(formatted_time)
                processed_data['temperature'].append(temperature)
                processed_data['distance'].append(distance)
                
            except Exception as e:
                logger.error(f"Error processing feed entry: {e}")
                continue

        return jsonify(processed_data)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Failed to load data"}), 500

if __name__ == '__main__':
    app.run(debug=True)