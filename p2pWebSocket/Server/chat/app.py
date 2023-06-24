from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import requests
import sys
import logging
from threading import Timer

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

MY_ADDRESS = ""
LINKS = {}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

with open(sys.argv[2]) as linkConfigFile:
    
    data = json.load(linkConfigFile)
    print(data[sys.argv[1]])
    print(data[sys.argv[1]]["id"])
    MY_ADDRESS = data[sys.argv[1]]["id"]
    LINKS = set(data[sys.argv[1]]["links"])
    
class P2PLink():
        
    def send(self,destination,message):
        
        message["header"] = ["P2PLink"] + message["header"]
        message["serverSender"] = MY_ADDRESS
        
        try:
            requests.post(f'http://{destination}/api/deliver', json=message)
        except ConnectionAbortedError:
            pass

class BestEffortBroadcast():
    
    def __init__(self,p2pLink):
        self.p2p = p2pLink
        
    def broadcast(self,message):
        
        message["header"] = ["BEBroadcast"] + message["header"]
        
        for link in LINKS.union({MY_ADDRESS}):
            self.p2p.send(link,message.copy())
            
class PerfectFailureDetector():
    
    def __init__(self,p2pLink,deltaTime):
        self.p2p = p2pLink
        self.alive = set(LINKS.copy())
        self.detected = set()
        #self.saluta()
        
        self.deltaTime = deltaTime
        self.timer = Timer(deltaTime, self.timeout)
        self.timer.start()
        
    def timeout(self):
        
        eprint("TIMEOUT!!")
        
        
        
        for process in LINKS:
            eprint(f"LNK{process}")
            if process not in self.alive and process not in self.detected:
                
                self.detected.add(process)
                self.emitCrash(process)
            
            
            self.p2p.send(process,{"header":["PFD"],"type": "HEARTBEAT_REQUEST"})
            
        
        self.alive = set()
        
        
        
        eprint("RESET!!")
        self.timer = Timer(self.deltaTime, self.timeout)
        self.timer.start()
        
    def sendHBReply(self,process):
        
        self.p2p.send(process,{"header":["PFD"],"type": "HEARTBEAT_REPLY"})
        
        
    def receiveHBReply(self,process):
        
        
        
        eprint(f"HBR{process}")
        self.alive.add(process)
        eprint(f"HBR{self.alive}")
        
        
    def emitCrash(self,process):
        
        for destination in self.alive:
            requests.post(f'http://{destination}/api/crash', json={"type":"CRASH","process":process})
          
        
p2p = P2PLink()
beb = BestEffortBroadcast(p2p)
pfd = PerfectFailureDetector(p2p,deltaTime=5.0)

@app.route('/')
def index():
    return render_template('index.html',SOCKET_PORT=sys.argv[1])

@app.route('/api/deliver', methods=['POST'])
def deliver_message():
    # Get the JSON message from the request body
    res = request.get_json()
    serverSender = res["serverSender"]
    eprint(f"MESSAGE: {res}")
    
    head = ""
    
    if res["header"]:
        
        head = res["header"].pop(0)
    
    else:
        return "not delivered"
        
    if head == "P2PLink":
    
        if serverSender != MY_ADDRESS and (not res["header"] or res["header"][0] == "BEBroadcast"):
            response = json.dumps(res)    
            socketio.emit('message', response, namespace = '/')
            #print("Delivered message by: ", res["id"])     
                   
        eprint(f"[{MY_ADDRESS}] P2P Link Delivery")
        
        requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        
        return "delivered"
    
    if head == "BEBroadcast":
        
        requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        
        eprint(f"[{MY_ADDRESS}] BEB Delivery")
        return "received"
    
    if head == "PFD":
        
        #requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        #response = json.dumps(res) 
        
        if res["type"] == "HEARTBEAT_REQUEST":
            
            pfd.sendHBReply(serverSender)
            eprint(f"[{MY_ADDRESS}] PFD Heartbeat Request Delivery from {serverSender}")
            return "received"
            
        if res["type"] == "HEARTBEAT_REPLY":
            
            pfd.receiveHBReply(serverSender)   
            
            eprint(f"[{MY_ADDRESS}] PFD Heartbeat Reply Delivery from {serverSender}")
            return "received"

@app.route('/api/crash', methods=['POST'])
def crash_message():
    # Get the JSON message from the request body
    res = request.get_json()
    eprint(f"CRASH_MESSAGE: {res}")
    
    if res["type"] == "CRASH":
        
        crashedProcess = res["process"]
        
        eprint("AAAAAAAAAAAAAAAAAAAAAAAAAA")
        eprint(f"Ha crashato {crashedProcess}")
        
        LINKS.remove(crashedProcess)
        
        return "crash_ACK"
    
    
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
