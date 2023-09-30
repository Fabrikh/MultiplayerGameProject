# MultiplayerGameProject

## How to start the system

Start by executing the Docker Deamon process.

Then, inside the folder *code*, execute the following command to build the code:

```console
docker-compose rm -f
docker-compose pull
docker-compose up --build
```

To access the login page, go to "http://localhost:3005/". Here you register a new account or login with one already existing. You will be then redirected to the game page.