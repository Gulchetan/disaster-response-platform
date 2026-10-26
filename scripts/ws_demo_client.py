"""Minimal WebSocket client: python -m scripts.ws_demo_client"""

import asyncio
import json

import websockets


async def main() -> None:
    uri = "ws://127.0.0.1:8000/ws/disasters"
    print(f"Connecting to {uri} ...")
    async with websockets.connect(uri) as ws:
        print("Listening for disaster_created / disaster_updated events (Ctrl+C to stop)")
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
