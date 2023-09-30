#import grequests
import requests
import os
from requests_futures.sessions import FuturesSession
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

import json
import random

import traceback


import sys
import logging
from threading import Timer,Lock

from time import sleep, time

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins='*')


MY_ADDRESS = ""
linksLock = Lock()
LINKS = {}
messageID = 0
idLock = Lock()
LOADBALANCER = ""
RNG = ""

lastDecision = None
decisionID = 0

openRooms = {}
closedRooms = {}
dice = {}

connected_clients = {}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
def startRecovery():
        
    with linksLock:
        for link in LINKS:
            eprint("SEND")
            session.post(f'http://{link}/api/recover', json={"type":"RECOVER","process":MY_ADDRESS})
            
    session.post(f'http://{LOADBALANCER}/api/recover', json={'process': MY_ADDRESS})

with open(sys.argv[2]) as linkConfigFile:

    data = json.load(linkConfigFile)
    print(data[sys.argv[1]])
    print(data[sys.argv[1]]["id"])
    MY_ADDRESS = data[sys.argv[1]]["id"]
    LINKS = set(data[sys.argv[1]]["links"])
    LOADBALANCER =data["loadbalancer"]
    RNG = data["rng"]

class P2PLink():

    def send(self,destination,message):

        message["header"] = ["P2PLink"] + message["header"]

        try:
            session = FuturesSession()
            session.post(f'http://{destination}/api/deliver', json=message)

        except Exception as e:

            eprint(f"[EXCEPTION] {type(e)} found!")
            eprint(e)
            traceback.print_exc()
            if type(e) == RuntimeError: sys.exit(1)
            
class BestEffortBroadcast():

    def __init__(self,p2pLink):
        self.p2p = p2pLink

    def broadcast(self,message):

        message["header"] = ["BEBroadcast"] + message["header"]

        with linksLock:
            for link in LINKS:
                self.p2p.send(link,message.copy())

class PerfectFailureDetector():

    def __init__(self,p2pLink,deltaTime):

        self.p2p = p2pLink
        self.alive = set(LINKS.copy())
        self.aliveLock = Lock()
        self.detected = set()
        self.deltaTime = deltaTime
        self.timer = Timer(deltaTime, self.timeout)
        self.timer.start()

    def timeout(self):


        with self.aliveLock:
            eprint("[PFD] Timeout!!")
            with linksLock:
                for process in LINKS:

                    if process not in self.alive and process not in self.detected:

                        self.detected.add(process)
                        self.emitCrash(process)


                    self.p2p.send(process,{"header":["PFD"],"type": "HEARTBEAT_REQUEST", "serverSender": MY_ADDRESS})


            self.alive = set()

            self.timer = Timer(self.deltaTime, self.timeout)
            self.timer.start()

    def sendHBReply(self,process):

        self.p2p.send(process,{"header":["PFD"],"type": "HEARTBEAT_REPLY", "serverSender": MY_ADDRESS})


    def receiveHBReply(self,process):

        #eprint(f"HBR{process}")
        self.alive.add(process)
        #eprint(f"HBR{self.alive}")


    def emitCrash(self,process):

        eprint(f"[EMITTING CRASH] {self.alive}")

        try:
            session = FuturesSession()
            session.post(f'http://{MY_ADDRESS}/api/crash', json={"type":"CRASH","process":process})
            session.post(f'http://{LOADBALANCER}/api/crash', json={'process': process})

        except Exception as e:

            eprint(f"[EXCEPTION] {type(e)} found!")
            eprint(e)
            
    def recovered(self,process):
        
        self.detected.discard(process)
        self.alive.add(process)

class ReliableBroadcast():

    def __init__ (self, beb, pfd):
        self.beb = beb
        self.pfd = pfd
        self.alive = set(LINKS.copy())
        self.aliveLock = Lock()
        self.fromP = {s: [] for s in LINKS}


    def broadcast(self, message):

        message["header"] = ["RBroadcast"] + message["header"]
        beb.broadcast(message)

    def deliver(self, message):
        sender = message["serverSender"]
        if sender in self.fromP:
            messages = self.fromP[sender]
            if self.check_message(message, messages):
                requests.post(f'http://{MY_ADDRESS}/api/deliver', json=message)
                self.fromP[sender].append(message)
                with self.aliveLock:
                    if sender not in self.alive:
                        beb.broadcast(message)

    def crashed(self, process):
        with self.aliveLock:
            self.alive.discard(process)
        if process in self.fromP:
            for message in self.fromP[process]:
                beb.broadcast(message)
                
    def recovered(self, process):
        with self.aliveLock:
            self.alive.add(process)
            if self.fromP[process]:
                self.fromP[process] = []

    def check_message(self, message, messages):
        for mex in messages:
            if mex["messageID"] == message["messageID"] and mex["serverSender"] == message["serverSender"]:
                return False
        return True

class Consensus():

    def __init__(self, beb, pfd):
        self.beb = beb
        self.pfd = pfd
        self.correct = set(LINKS.copy())
        self.correct.add(MY_ADDRESS)
        self.correctLock = Lock()
        self.received_from = []
        self.received_from.append(set(LINKS.copy()))
        self.received_from[0].add(MY_ADDRESS)
        self.proposals = []
        self.proposals.append(set())
        self.decision = None
        self.round = 1

    def crashed(self, process):
        with self.correctLock:
            self.correct.discard(process)
            
    def recovered(self, process):
        with self.correctLock:
            self.correct.add(process)

    def propose_value(self, value, id, socket, sender):
        eprint(f"[CONSENSUS] proposal: {value}")

        self.proposals.append(set())

        self.proposals[1].add(value)
        valueData = json.dumps(list(self.proposals[1]))
        proposal = {"header": [], "type": "PROPOSAL",  "serverSender": MY_ADDRESS, "round": 1, "value": valueData, "id": decisionID, "proposedId": id, "socket": socket, "starter": sender}
        beb.broadcast(proposal)

    def deliver_proposal(self, message):
        eprint("[CONSENSUS] deliver propose")
        sender = message["serverSender"]
        value = set(json.loads(message["value"]))
        round = message["round"]

        try:
            _ = self.received_from[round]
        except IndexError:
            self.received_from.append(set())

        try:
            _ = self.proposals[round]
        except IndexError:
            self.proposals.append(set())

        self.received_from[round].add(sender)
        self.proposals[round].update(value)
        if set(self.correct).issubset(set(self.received_from[round])) and self.decision == None:
            self.decide_min(message)

    def deliver_decided(self, message):
        if message["id"] == decisionID:
            eprint("[CONSENSUS] deliver decide")
            if message["serverSender"] in self.correct and message["serverSender"] != MY_ADDRESS:
                if self.decision == None:
                    value = message["value"]
                    self.decision = value
                    decision_value = {"header": [], "type": "DECIDED", "value": value,  "serverSender": MY_ADDRESS, "id": decisionID, "proposedId": message["proposedId"], "socket": message["socket"], "starter": message["starter"]}
                    beb.broadcast(decision_value)
                    self.decide(self.decision, decision_value)


    def choose(prop):

        # Choose a common value for everyone

        proposals = list(map(lambda x: json.loads(x),prop))
        eprint("[CONSENSUS PROPOSALS] ##",proposals)

        if type(proposals[0]) == int:
            return min(proposals)

        if type(proposals[0]) == list or type(proposals[0]) == set:
            return proposals[random.randint(0,len(proposals)-1)]


    def decide_min(self, message):

        try:
            _ = self.received_from[self.round]
            _ = self.proposals[self.round]

            if self.received_from[self.round] == self.received_from[self.round-1]:
                self.decision = Consensus.choose(self.proposals[self.round])
                decision_value = {"header": [], "type": "DECIDED", "value": self.decision,  "serverSender": MY_ADDRESS, "id": decisionID, "proposedId": message["proposedId"], "socket": message["socket"], "starter": message["starter"]}
                beb.broadcast(decision_value)
                self.decide(self.decision, message)
            else:
                self.round = self.round + 1
                valueData = json.dumps(list(self.proposals[self.round - 1]))
                proposal = {"header": [], "type": "PROPOSAL",  "serverSender": MY_ADDRESS, "round": self.round, "value": valueData, "id": decisionID, "proposedId": message["proposedId"], "socket": message["socket"], "starter": message["starter"]}
                beb.broadcast(proposal)

        except IndexError:
            eprint("[EXCEPTION] INDEX found!")

    def decide(self, decision_value, message):
        eprint(f"[DECIDED VALUE] {decision_value}")

        try:
            session = FuturesSession()
            session.post(f'http://{MY_ADDRESS}/api/consensus', json={"type":"DECISION","decision":decision_value, "proposedId": message["proposedId"], "socket": message["socket"], "starter": message["starter"]})

        except Exception as e:

            eprint(f"[EXCEPTION] {type(e)} found!")
            eprint(e)


    def reset(self):
        self.correct = set(LINKS.copy())
        self.correct.add(MY_ADDRESS)
        self.correctLock = Lock()
        self.received_from = []
        self.received_from.append(set(LINKS.copy()))
        self.received_from[0].add(MY_ADDRESS)
        self.proposals = []
        self.proposals.append(set())
        self.decision = None
        self.round = 1


p2p = P2PLink()
beb = BestEffortBroadcast(p2p)
pfd = PerfectFailureDetector(p2p,deltaTime=5.0)
rb = ReliableBroadcast(beb, pfd)
consensus = Consensus(beb, pfd)

session = FuturesSession()



startRecovery()

class Rng():
    def __init__(self):
        self.dice1 = self.generate_random_number()
        self.dice2 = self.generate_random_number()

    def generate_random_number(self):
        return requests.get(f'http://{RNG}/api/random').json()["random_number"]
    
    def random_dice(self, caller):
        res = [self.dice1, self.dice2]

        self.dice1 = self.generate_random_number()
        self.dice2 = self.generate_random_number()
                
        eprint(res)
        return res

rng = Rng()

class Room():
    def __init__ (self, roomId, startId):
        self.roomId = roomId
        self.players = {startId[0]}
        self.socketsToUsers = {}
        self.socketsToUsers[startId[0]] = startId[1]
        self.open = True
        self.turn = 0
        self.timer = Timer(20.0, self.endTurn)
        self.bets = {}
        self.placedBet = {}
        self.bets2 = {}
        self.placedBet2 = {}
        self.points = {}
        self.points[startId[1]] = 100
        self.endOfGame = False

    def close(self):
        self.open = False
        close_the_room(self.roomId)
        self.startGame()

    def openRoom(self):
        self.open = True
        self.endOfGame = False
        open_the_room(self.roomId)

    def newPlayer(self, newId):

        self.players.add(newId[0])
        self.socketsToUsers[newId[0]] = newId[1]
        self.points[newId[1]] = 100
        eprint(self.players)

    def removePlayer(self, playerId):
        self.players.discard(playerId[0])
        self.socketsToUsers.pop(playerId[0], None)
        self.points.pop(playerId[1], None)
        self.bets.pop(playerId[0], None)
        self.placedBet.pop(playerId[0], None)
        if self.endOfGame:
            if len(self.players) < 3:
                self.openRoom()


    def checkClosure(self):
        if len(self.players) >= 3:
            self.close()

    def getPlayers(self):
        return list(self.socketsToUsers.items())

    def startGame(self):
        res = {"type" : "START", "points" : self.points}
        for sockets in self.players:
            socketio.emit('message', json.dumps(res), room=sockets)
        self.timer = Timer(20.0, self.endTurn)
        self.timer.start()

    def endTurn(self):
        eprint("ENDEDTURN")
        self.turn += 1

        ### RNG ###
        global dice

        if MY_ADDRESS in self.roomId:
            result = rng.random_dice((MY_ADDRESS, self.roomId))
            dice1 = result[0]
            dice2 = result[1]
            total = sum(result)

            global messageID
            message = {"header": [], "type": "RNG", "serverSender": MY_ADDRESS, "messageID": None, "roomId": self.roomId, "dice1": dice1, "dice2": dice2}
            with idLock:
                message["messageID"] = messageID
                messageID += 1            
            rb.broadcast(message)
        else:
            dice1_2 = dice.get(self.roomId, None)

            while dice1_2 == None:
                dice1_2 = dice.get(self.roomId, None)
            
            dice1 = dice1_2[0]
            dice2 = dice1_2[1]
            total = sum([dice1, dice2])
        ###########

        for sockets in self.players:
            res = {"type" : "DICE", "dice1": dice1, "dice2": dice2}
            socketio.emit('message', json.dumps(res), room=sockets)

        sleep(6)

        eprint(total)

        for player in self.bets:
            if total%2 == 0:
                if self.bets[player] == "EVEN":
                    self.points[self.socketsToUsers[player]] += 2 * int(self.placedBet[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet[player])
            else:
                if self.bets[player] == "ODD":
                    self.points[self.socketsToUsers[player]] += 2 * int(self.placedBet[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet[player])
        for player in self.bets2:
            if total==2:
                if self.bets2[player] == "TWO":
                    self.points[self.socketsToUsers[player]] += 18 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==3:
                if self.bets2[player] == "THREE":
                    self.points[self.socketsToUsers[player]] += 9 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==4:
                if self.bets2[player] == "FOUR":
                    self.points[self.socketsToUsers[player]] += 6 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==5:
                if self.bets2[player] == "FIVE":
                    self.points[self.socketsToUsers[player]] += 5 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==6:
                if self.bets2[player] == "SIX":
                    self.points[self.socketsToUsers[player]] += 4 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==7:
                if self.bets2[player] == "SEVEN":
                    self.points[self.socketsToUsers[player]] += 3 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==8:
                if self.bets2[player] == "EIGHT":
                    self.points[self.socketsToUsers[player]] += 4 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==9:
                if self.bets2[player] == "NINE":
                    self.points[self.socketsToUsers[player]] += 5 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==10:
                if self.bets2[player] == "TEN":
                    self.points[self.socketsToUsers[player]] += 6 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==11:
                if self.bets2[player] == "ELEVEN":
                    self.points[self.socketsToUsers[player]] += 9 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])
            elif total==12:
                if self.bets2[player] == "TWELVE":
                    self.points[self.socketsToUsers[player]] += 18 * int(self.placedBet2[player])
                else:
                    self.points[self.socketsToUsers[player]] -= int(self.placedBet2[player])

        for sockets in self.players:
            res = {"type" : "ENDTURN", "points": self.points, "total": total}
            socketio.emit('message', json.dumps(res), room=sockets)

        self.bets = {}
        self.bets2 = {}

        if self.turn < 5:
            self.timer = Timer(20.0, self.endTurn)
            self.timer.start()
        else:
            self.end()


    def receiveBet(self, player, bet, placedBet, bet2, placedBet2):
        self.bets[player] = bet
        self.placedBet[player] = placedBet
        self.bets2[player] = bet2
        self.placedBet2[player] = placedBet2

    def end(self):
        eprint("END GAME")
        self.endOfGame = True
        for sockets in self.players:
            res = {"type" : "ENDGAME", "points": self.points}
            socketio.emit('message', json.dumps(res), room=sockets)
        
        self.turn = 0
        self.bets = {}
        self.placedBet = {}
        self.bets2 = {}
        self.placedBet2 = {}
        
        for players in self.points:
            self.points[players] = 100
        

        self.timer = Timer(20.0, self.restart)
        self.timer.start()
    
    def restart(self):
        if self.endOfGame:
            self.startGame()



@app.route('/')
def index():
    #eprint(f"RICHIESTA", request.args.get('redirected'))
    #eprint(f"LOCAL ADDR", request.remote_addr)
    username = request.cookies.get('username')  
    if(request.args.get('redirected')):
        if(not username):
            return render_template('login.html', SOCKET_PORT=sys.argv[1], cookies=username)
        else:
            return render_template('index.html', SOCKET_PORT=sys.argv[1], cookies=username)

@app.route('/register')
def register():
   return render_template('register.html')
    

@app.route('/api/deliver', methods=['POST'])
def deliver_message():
    global messageID
    global openRooms
    global dice
    # Get the JSON message from the request body
    res = request.get_json()
    serverSender = res["serverSender"]
    #eprint(f"MESSAGE: {res}")

    head = ""

    if res["header"]:

        head = res["header"].pop(0)

    else:
        return "not delivered"

    if head == "P2PLink":

        #eprint(f"[{MY_ADDRESS}] P2P Link Delivery")

        requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)

        return "delivered"

    if head == "BEBroadcast":

        if res["type"] == "RESPONSE" or res["type"] == "DISCONNECTION" or res["type"] == "NEWROOM" or res["type"] == "ADDTOROOM" or res["type"] == "LEAVETHEROOM" or res["type"] == "GAMEMOVE":
            rb.deliver(res)

        if res["type"] == "STARTPROPOSAL":
            eprint(f"CHECK {res['id']}")
            isValid = res["id"] in connected_clients.values()
            if isValid:
                consensus.propose_value(json.dumps(0), res["id"], res["socket"], res["starter"])
            else:
                consensus.propose_value(json.dumps(1), res["id"], res["socket"], res["starter"])

        if res["type"] == "PROPOSAL":
            consensus.deliver_proposal(res)

        if res["type"] == "DECIDED":
            consensus.deliver_decided(res)
        
        if res["type"] == "RNG":
            rb.deliver(res)

        #eprint(f"[{MY_ADDRESS}] BEB Delivery")
        return "received"

    if head == "PFD":

        #requests.post(f'http://{MY_ADDRESS}/api/deliver', json=res)
        #response = json.dumps(res)

        if res["type"] == "HEARTBEAT_REQUEST":

            pfd.sendHBReply(serverSender)
            #eprint(f"[{MY_ADDRESS}] PFD Heartbeat Request Delivery from {serverSender}")
            return "received"

        if res["type"] == "HEARTBEAT_REPLY":

            with pfd.aliveLock:
                pfd.receiveHBReply(serverSender)

            #eprint(f"[{MY_ADDRESS}] PFD Heartbeat Reply Delivery from {serverSender}")
            return "received"

    if head == "RBroadcast":

        if res["type"] == "NEWROOM" or res["type"] == "ADDTOROOM":  #Either way, the set default generates a room if there isn't one with that id or just adds a value if not

            if res["roomId"] not in openRooms:
                openRooms[res["roomId"]] = Room(res["roomId"], res["startId"])

            openRooms[res["roomId"]].newPlayer(res["startId"])
            for listId in res["listId"]:
                openRooms[res["roomId"]].newPlayer(listId)
            newres = { "type": "ROOM", "roomId": res["roomId"], "user": res["user"]}
            playerlist = openRooms[res["roomId"]].getPlayers()
            for sockets in playerlist:
                socketio.emit('message', json.dumps(newres), room=sockets[0])
            openRooms[res["roomId"]].checkClosure()

        elif res["type"] == "GAMEMOVE":
            closedRooms[res["roomId"]].receiveBet(res["startId"], res["bet"], res["placedBet"], res["bet2"], res["placedBet2"])
        
        elif res["type"] == "LEAVETHEROOM":
            newres = { "type": "LEFTROOM", "roomId": res["roomId"], "user": res["user"]}
            if res["roomId"] in openRooms:
                playerlist = openRooms[res["roomId"]].getPlayers()
                openRooms[res["roomId"]].removePlayer(res["startId"])
                for sockets in playerlist:
                    socketio.emit('message', json.dumps(newres), room=sockets[0])
                
            elif res["roomId"] in closedRooms:
                playerlist = closedRooms[res["roomId"]].getPlayers()
                closedRooms[res["roomId"]].removePlayer(res["startId"])
                for sockets in playerlist:
                    socketio.emit('message', json.dumps(newres), room=sockets[0])
            
        elif res["type"] == "RNG":
            dice[res["roomId"]] = (res["dice1"], res["dice2"])

        else:
            response = json.dumps(res)
            socketio.emit('message', response, namespace = '/')
        #print("Delivered message by: ", res["id"])

        #eprint(f"[{MY_ADDRESS}] RB Delivery")
        return "received"


@app.route('/api/crash', methods=['POST'])
def crash_message():
    # Get the JSON message from the request body
    res = request.get_json()
    #eprint(f"CRASH_MESSAGE: {res}")

    if res["type"] == "CRASH":

        crashedProcess = res["process"]

        eprint(f"[CRASH NOTIFICATION] Ha crashato {crashedProcess}")

        with linksLock:
            LINKS.discard(crashedProcess)

        consensus.crashed(crashedProcess)
        rb.crashed(crashedProcess)

        return "crash_ACK"
    
@app.route('/api/recover', methods=['POST'])
def recover_message():
    # Get the JSON message from the request body
    res = request.get_json()
    #eprint(f"CRASH_MESSAGE: {res}")

    if res["type"] == "RECOVER":

        recoveredProcess = res["process"]

        eprint(f"[RECOVER NOTIFICATION] Ha recuperato {recoveredProcess}")

        with linksLock:
            LINKS.add(recoveredProcess)
            pfd.recovered(recoveredProcess)

        consensus.recovered(recoveredProcess)
        rb.recovered(recoveredProcess)

        return "recover_ACK"

@app.route('/api/consensus', methods=['POST'])
def decision_message():
    global lastDecision
    global decisionID
    global messageID
    # Get the JSON message from the request body
    res = request.get_json()
    #eprint(f"CRASH_MESSAGE: {res}")

    if res["type"] == "DECISION":

        lastDecision = res["decision"]

        eprint(f"[CONSENSUS NOTIFICATION] Scelto il valore: {lastDecision}")

        decisionID += 1

        eprint(f"decided: {res['proposedId']} with {res['decision']}")
        if(res["starter"] and res["starter"] == MY_ADDRESS):
            if(res['decision'] == 0):
                        response = { "type": "INVALID", "message": "Username " + res["proposedId"] + " already in use!"}
                        socketio.emit('message', json.dumps(response), room=res["socket"])
            else:
                if(res["starter"] and res["starter"] == MY_ADDRESS):
                    connected_clients[res["socket"]] = res["proposedId"]
                res = { "type": "RESPONSE", "message": "User " + res["proposedId"] + " connected to the chat!", "id": "all" }
                #print("Received message:" + mex["message"] + " by ID: " + mex["id"])

                response = json.dumps(res)
                res["header"] = []
                res["serverSender"] = MY_ADDRESS
                with idLock:
                    res["messageID"] = messageID
                    messageID += 1
                rb.broadcast(res)
        consensus.reset()

        return "decision_ACK"

@socketio.on('connect')
def handle_connection():


    try:
        eprint(f"[CLIENT CONNECTED]")

        session = FuturesSession()
        session.post(f'http://{LOADBALANCER}/api/connection', json={'port': MY_ADDRESS})

    except Exception as e:

        eprint(f"[EXCEPTION] {type(e)} found!")
        eprint(e)



def create_room(startId, user):
    id = str(time()) + "&&" + MY_ADDRESS
    USER = (startId, user)
    openRooms[id] = Room(id, USER)
    res = { "type" : "NEWROOM", "roomId" : id, "starter": MY_ADDRESS, "startId": USER, "listId": [USER], "user" : user}
    return res

def add_to_room(startId, user):
    USER = (startId, user)
    for roomId in openRooms:
        res = { "type" : "ADDTOROOM", "roomId" : roomId, "starter": MY_ADDRESS, "startId": USER, "listId": openRooms[roomId].getPlayers(), "user" : user}
        return res

def close_the_room(roomId):
    closedRooms[roomId] = openRooms.pop(roomId, None)

def open_the_room(roomId):
    openRooms[roomId] = closedRooms.pop(roomId, None)

def leave_the_room(startId, user):
    USER = (startId, user)
    for roomId in openRooms:
        if USER in openRooms[roomId].getPlayers():
            res = { "type" : "LEAVETHEROOM", "roomId" : roomId, "starter": MY_ADDRESS, "startId": USER, "user" : user}
            return res
        
    for roomId in closedRooms:
        if USER in closedRooms[roomId].getPlayers():
            res = { "type" : "LEAVETHEROOM", "roomId" : roomId, "starter": MY_ADDRESS, "startId": USER, "user" : user}
            return res
    return None


@socketio.on('message')
def handle_message(message):

    global messageID

    mex = json.loads(message)
    if mex["type"] == "CONNECTION":
        client_id = request.sid  # Get the unique ID of the connected socket
        if(mex["id"] in connected_clients.values()):
            res = { "type": "INVALID", "message": "Username " + mex["id"] + " already in use!"}
            socketio.emit('message', json.dumps(res), room=client_id)
        else:
            res = { "type": "STARTPROPOSAL", "id": mex["id"], "socket": client_id, "starter": MY_ADDRESS}

            #connected_clients[client_id] = mex["id"]
            #res = { "type": "RESPONSE", "message": "User " + mex["id"] + " connected to the chat!", "id": "all" }

    elif mex["type"] == "SEARCHGAME":
        if not openRooms:
            res = create_room(request.sid, mex["id"])

        else:
            res = add_to_room(request.sid, mex["id"])

    elif mex["type"] == "LEAVEGAME":
        res = leave_the_room(request.sid, mex["id"])
        if res == None:
            return None

    elif mex["type"] == "GAME_MOVE":
        res = {"type": "GAMEMOVE", "roomId": mex["roomId"], "bet": mex["bet"], "placedBet": mex["placedBet"], "bet2": mex["bet2"], "placedBet2": mex["placedBet2"], "startId": request.sid}
    else:
        res = { "type": "RESPONSE", "message": mex["message"], "id": mex["id"], "avatar": mex["avatar"] }

    #print("Received message:" + mex["message"] + " by ID: " + mex["id"])

        ## send message outside

    res["header"] = []
    res["serverSender"] = MY_ADDRESS

    with idLock:
        res["messageID"] = messageID
        messageID += 1

        #eprint(f"MSG: {res}")

        # TEST CONSENSUS
        #consensus.propose_value(json.dumps(random.randint(0,100)))
        #consensus.propose_value(json.dumps([random.randint(0,100) for i in range(3)]))
    eprint(res)
    rb.broadcast(res)

        #p2p.send(LINKS[0],res)


@socketio.on('disconnect')
def handle_disconnect():
    global messageID
    client_id = request.sid
    username = connected_clients[client_id]
    connected_clients.pop(client_id, None)

    res = { "type": "DISCONNECTION", "message": "User " + username + " disconnected from the chat!", "id": "all" }

    response = json.dumps(res)
    socketio.emit('message', response)

        ## send message outside

    res["header"] = []
    res["serverSender"] = MY_ADDRESS

    with idLock:
        res["messageID"] = messageID
        messageID += 1

        #eprint(f"MSG: {res}")

    rb.broadcast(res)


if __name__ == '__main__':

    if len(sys.argv) == 3:

        socketio.run(app, host='0.0.0.0', port=sys.argv[1], allow_unsafe_werkzeug=True)
        
        
        
        
    else:

        raise Exception("Wrong number of arguments provided!")