from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import requests
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

links = []

with open("./config/links.json") as linkConfigFile:
    
    data = json.load(linkConfigFile)
    links = data[sys.argv[1]]
    print(links)
    

@app.route('/')
def index():
    return render_template('index.html',SOCKET_PORT=sys.argv[1])

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

    for link in links:
        response = requests.post(f'http://{link}/api/send', json=res)


if __name__ == '__main__':
    
    if len(sys.argv) == 2:
               
        socketio.run(app, host='0.0.0.0', port=sys.argv[1])
    else:
        
        raise Exception("Wrong number of arguments provided!")
