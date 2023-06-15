from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import requests
import sys
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

MY_ADDRESS = ""
LINKS = []

with open(sys.argv[2]) as linkConfigFile:
    
    data = json.load(linkConfigFile)
    print(data[sys.argv[1]])
    print(data[sys.argv[1]]["id"])
    MY_ADDRESS = data[sys.argv[1]]["id"]
    LINKS = data[sys.argv[1]]["links"]
    
class P2PLink():
        
    def send(self,destination,message):
        
        message["header"] = ["P2PLink"]
        message["serverSender"] = MY_ADDRESS
        
        requests.post(f'http://{destination}/api/deliver', json=message)

class BestEffortBroadcast():
    
    def __init__(self,p2pLink):
        self.p2p = p2pLink
        
    def broadcast(self,message):
        
        message["header"] = ["BEBroadcast"] + message["header"]
        
        for link in LINKS + [MY_ADDRESS]:
            p2p.send(link,message)
          
        
p2p = P2PLink()
beb = BestEffortBroadcast(p2p)

@app.route('/')
def index():
    return render_template('index.html',SOCKET_PORT=sys.argv[1])

@app.route('/api/deliver', methods=['POST'])
def deliver_message():
    # Get the JSON message from the request body
    res = request.get_json()
    serverSender = res["serverSender"]
    print(res)
    
    head = ""
    
    if res["header"]:
        
        head = res["header"].pop(0)
    
    else:
        return "not delivered"
        
    if head == "P2PLink":
    
        if serverSender != MY_ADDRESS:
            response = json.dumps(res)    
            socketio.emit('message', response, namespace = '/')
            #print("Delivered message by: ", res["id"])
            
        print("P2P Link Delivery")
        requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        
        return "delivered"
    
    if head == "BEBroadcast":
        
        requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        
        print("delivered")
        return "received"
    

@socketio.on('message')
def handle_message(message):
    mex = json.loads(message)
    if(mex["type"] == "CONNECTION"):
        res = { "type": "RESPONSE", "message": "User " + mex["id"] + " connected to the chat!", "id": "all" }

    else:
        res = { "type": "RESPONSE", "message": mex["message"], "id": mex["id"] }

    #print("Received message:" + mex["message"] + " by ID: " + mex["id"])

    response = json.dumps(res)
    socketio.emit('message', response)
    
    ## send message outside
    
    res["header"] = []
    
    beb.broadcast(res)
    #p2p.send(LINKS[0],res)


if __name__ == '__main__':
    
    if len(sys.argv) == 3:
               
        socketio.run(app, host='0.0.0.0', port=sys.argv[1], allow_unsafe_werkzeug=True)
    else:
        
        raise Exception("Wrong number of arguments provided!")
