import asyncio
import json
import websockets

async def test_chat():
    session_id = "00000000-0000-0000-0000-000000000000"
    token = "sandbox-token"
    uri = f"ws://localhost:8000/ws/chat/{session_id}?token={token}"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # Send a message
        payload = {
            "type": "message",
            "payload": {
                "content": "Hi, what are the specs of T001?"
            }
        }
        print(f"Sending message: {payload}")
        await websocket.send(json.dumps(payload))
        
        # Listen for messages
        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received frame: {data}")
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed cleanly.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
