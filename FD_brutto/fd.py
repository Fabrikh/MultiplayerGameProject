from flask import Flask, jsonify, request
import requests
import signal
import threading

app = Flask(__name__)

#######################
### FD uses P2PLink ###
#######################

P2PLINK = 'http://localhost:5000/api/'

pi = ["1","2","3","4","5","6","7","8","9","10"] # Lista dei nodi
alive = ["1","2","3","4","5","6","7","8","9","10"] # Lista dei nodi vivi
detected = [] # Lista dei nodi morti
TIMEOUT = 5



def timeout_handler(signum, frame):
    # This function will be called when the timeout is reached

    global pi, alive, detected

    for p in pi:
        if p not in alive and p not in detected:
            detected.append(p)
            print("Node " + p + " is dead") # trigger crash!!
        requests.post(P2PLINK + 'send', json = {"source":"FD", "destination":p, "content":"HEARTBEATREQUEST"})
        print("Sent message HEARTBEATREQUEST",  "from FD", "to", p)

    alive = []
    signal.alarm(TIMEOUT)

def detect_failures():
    # Perform some long-running operation here

    while(True):
        message = requests.get(P2PLINK + 'deliver?id=FD').json()
        p = message["source"]
        print(p)
        if p != "none" and p not in alive:
            alive.append(p)
            print("Node " + str(p) + " is alive")


""" @app.route('/api/HEARTBEAT_REQUEST', methods=['POST'])
def heartbeat_request():
    requests.post(P2PLINK + 'send', json = {"source":"FD", "destination":p, "content":"HEARTBEATREQUEST"}) """

@app.route('/api/HEARTBEAT_REPLY', methods=['POST'])
def heartbeat_reply():
    # Get source from request
    source = request.args.get('id')
    requests.post(P2PLINK + 'send', json = {"source":source, "destination":"FD", "content":"HEARTBEATREPLY"})


if __name__ == '__main__':
    # Set the signal handler and specify the timeout value
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT)

    # Start the failure detection thread
    failure_detection_thread = threading.Thread(target=detect_failures)
    failure_detection_thread.start()

    # app.run(debug=True, host='0.0.0.0', port=5002)