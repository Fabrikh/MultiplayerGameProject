from flask import Flask, request
import requests

# List of processes (to be implemented)
pi = ['p1','p2','p3','p4','p5']

# Pp2pLink API
p2pLink = 'http://p2p-link:5000/api/'

app = Flask(__name__)

###########################################################
######### BEB API FOR SERVER-SERVER COMMUNICATION #########
###########################################################

@app.route('/api/BEB_Broadcast', methods=['POST'])
def BEB_Broadcast():
    # Get message from request
    message = request.json

    source = message["source"]
    destination = message["destination"]
    m = message["content"]

    # Check if destination is BEB
    if destination != "BEB":
        return {"error":"Destination must be BEB"}
    else:
        # Broadcast message to all processes
        for p in pi:
            requests.post(p2pLink + 'send', json = {"source":source, "destination":p, "content":m})
            print("Sent message", m,  "from", source, "to", p)

        return {"broadcast":True}

@app.route('/api/BEB_Deliver', methods=['GET'])
def BEB_Deliver():
    # Get destination from request
    destination = request.args.get('id')

    response = requests.get(p2pLink + 'deliver?id=' + destination)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)