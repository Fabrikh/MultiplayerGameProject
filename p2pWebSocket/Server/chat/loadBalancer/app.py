from flask import Flask, request, jsonify, redirect
import requests
import sys
import json
import re

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

    while SERVERS:
        SERVER = min(SERVERS, key=SERVERS.get)

        # Forward the request to the least busy server
        
        target_url = "http://localhost" + re.search(":[0-9]*",SERVER).group()
        
        try:
            #response = requests.get(target_url + request.path + "?redirected=true")
            return redirect(target_url + request.path + "?redirected=true", code=302)
        except Exception as e:
            SERVERS.pop(SERVER, None)

    # Update the connection count for the least busy server
    #SERVERS[SERVER] += 1
    return "We don't have another server, if you want to play, please wait"
    

@app.route('/api/disconnection', methods=['POST'])
def decrease_value():
    eprint(f"DISCONNECTION")
    res = request.get_json()

    if res['port']:

        SERVERS[res['port']] -= 1
    
    for servers in SERVERS:
        eprint(f"CONNECTED VALUES: {servers} - {SERVERS[servers]}")

    return "Decreased"

@app.route('/api/connection', methods=['POST'])
def increase_value():
    eprint(f"CONNECTION")
    res = request.get_json()

    if res['port']:

        SERVERS[res['port']] += 1
    
    for servers in SERVERS:
        eprint(f"CONNECTED VALUES: {servers} - {SERVERS[servers]}")

    return "Increased"

@app.route('/api/crash', methods=['POST'])
def handle_crash():
    eprint(f"CRASH")
    res = request.get_json()

    if res['process']:

        SERVERS.pop(res['process'], None)
    
    for servers in SERVERS:
        eprint(f"CONNECTED VALUES: {servers} - {SERVERS[servers]}")

    return "Increased"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3005)
