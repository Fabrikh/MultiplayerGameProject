# MultiplayerGameProject

## Prova app e appPy

PRIMO COMANDO PER CREARE IL NETWORK:
```console
docker network create my-network
```
SECONDO E TERZO COMANDO PER CREARE IL PRIMO DOCKER E AVVIARLO:
```console
docker build -t nodejs-app .
docker run -p 3000:3000 --network my-network --name nodejs-container nodejs-app
```
IDEM PER IL SECONDO DOCKER:
```console
docker build -t flask-app .
docker run -p 5000:5000 --network my-network --name flask-container flask-app
```
Per provare il funzionamento basta connettersi a "http://localhost:5000/api/receive" per vedere un messaggio esposto sulla flask app e generato dalla nodejs app

## Prova p2pLink

All'interno della cartella p2pLink/server, eseguire i comandi:

```console
docker network create my-network
docker build -t flask-app .
docker run -p 5000:5000 --network my-network --name p2p-link flask-app
```

Se tutto va bene, dovresti avere un docker funzionante chiamato p2p-link.

Per inviare un messaggio, puoi inviare una post request a "http://localhost:5000/api/send". Il messaggio è un json con il seguente formato.

{
    "source":"Adam",
    "destination":"Bob",
    "content":"Hello world"
}

Per ricevere l'ultimo messaggio ricevuto, si fa una get request del tipo "http://localhost:5000/api/deliver?id=Bob"

## Prova p2pWebSocket

Per avviare con docker, eseguire i comandi in Server/chat

```console
docker-compose rm -f
docker-compose pull
docker-compose up --build -d
```

Per accedere con i client, andare rispettivamente su

"http://localhost:3000/"

"http://localhost:3001/"

"http://localhost:3002/"

Per avviare un server in locale (eg. su porta 3000), il comando è 

```console
python app.py 3000 ./config/linksLocal.json
```

## Prova beb

Build and run p2p before beb

cd into /beb

```console
docker network create my-network
docker build -t flask-app .
docker run -p 5001:5001 --network my-network --name beb flask-app
```

To test beb:
Send a message like { "source":"Adam", "destination":"BEB", "content":"Hello world" } to "http://localhost:5001/api/BEB_Broadcast"
Now you can deliver the message from any process id in "pi" list like "http://localhost:5001/api/BEB_Deliver?id=p1"