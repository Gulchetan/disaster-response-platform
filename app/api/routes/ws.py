from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.realtime import realtime_hub

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/disasters")
async def disasters_websocket(websocket: WebSocket) -> None:
    await realtime_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await realtime_hub.disconnect(websocket)
