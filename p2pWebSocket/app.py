import asyncio
import websockets
import json

async def handle_message(websocket, path):
    async for message in websocket:
        mex = json.loads(message)

        if(mex["type"] == "CONNECTION"):
            res = { "type": "RESPONSE", "message": "User " + mex["id"] + " connected to the chat!", "id": "all" }

        else:
            res = { "type": "RESPONSE", "message": "Received: " + mex["message"], "id": mex["id"] }

        print("Received message:", mex["message"])

        response = json.dumps(res)
        await websocket.send(response)

start_server = websockets.serve(handle_message, 'localhost', 8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()