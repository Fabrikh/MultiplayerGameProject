from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/api/send', methods=['POST'])
def send_message():
    # Get the JSON message from the request body
    message = request.get_json()

    # Send the message to the Node.js container
    response = requests.post('http://nodejs-container:3000/api/send', json=message)

    return jsonify(response.json())

@app.route('/api/receive', methods=['GET'])
def receive_message():
    # Request the message from the Node.js container
    response = requests.get('http://nodejs-container:3000/api/receive')

    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
