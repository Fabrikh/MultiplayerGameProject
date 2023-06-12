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

Il server non si avvia ancora con Docker. Per ora provare con l'ambiente virtuale Python .venv.

Per avviare il server sulla porta 3000 (ad esempio), basta eseguire:

```console
python app.py 3000
```

A questo punto il client si aprirà su "http://localhost:3000".

Il file config/links.json descrive i collegamenti tra i server 3000,3001 e 3002. Si possono modificare a proprio piacimento.