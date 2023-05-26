# MultiplayerGameProject

PRIMO COMANDO PER CREARE IL NETWORK: 
docker network create my-network

SECONDO E TERZO COMANDO PER CREARE IL PRIMO DOCKER E AVVIARLO:
docker build -t nodejs-app .
docker run -p 3000:3000 --network my-network --name nodejs-container nodejs-app

IDEM PER IL SECONDO DOCKER:
docker build -t flask-app .
docker run -p 5000:5000 --network my-network --name flask-container flask-app

Per provare il funzionamento basta connettersi a "http://localhost:5000/api/receive" per vedere un messaggio esposto sulla flask app e generato dalla nodejs app
