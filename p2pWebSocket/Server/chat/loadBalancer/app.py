from flask import Flask, request, jsonify
import requests
import sys
import json

app = Flask(__name__)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

with open(sys.argv[1]) as linkConfigFile:

    data = json.load(linkConfigFile)
    LINKS = set(data["links"])

# Dictionary to store active connections for each server
SERVERS = dict(zip(LINKS, [0] * len(LINKS)))

@app.route('/')
def redirect_request():
    # Find the least busy server
    SERVER = min(SERVERS, key=SERVERS.get)

    # Forward the request to the least busy server
    target_url = f"http://{SERVER}"
    response = requests.get(target_url + request.path)
    
    # Update the connection count for the least busy server
    SERVERS[SERVER] += 1

    return response.text, response.status_code

@app.route('/api/disconnection', methods=['POST'])
def decrease_value():
    eprint(f"DISCONNECTION")
    res = request.get_json()

    if res['port']:

        SERVERS[res['port']] -= 1
    
    for servers in SERVERS:
        eprint(f"CONNECTED VALUES: {servers} - {SERVERS[servers]}")

    return "Decreased"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3005)
