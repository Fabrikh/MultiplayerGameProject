from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/send', methods=['POST'])
def send_message():
    # Get the JSON message from the request body
    res = request.get_json()
    response = json.dumps(res)
    socketio.emit('message', response, namespace = '/')
    print("Received message by: ", res["id"])
    return "received"

@socketio.on('message')
def handle_message(message):
    mex = json.loads(message)
    if(mex["type"] == "CONNECTION"):
        res = { "type": "RESPONSE", "message": "User " + mex["id"] + " connected to the chat!", "id": "all" }

    else:
        res = { "type": "RESPONSE", "message": mex["message"], "id": mex["id"] }

    print("Received message:" + mex["message"] + " by ID: " + mex["id"])

    response = json.dumps(res)
    socketio.emit('message', response)

    response = requests.post('http://localhost:3000/api/send', json=res)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3001)