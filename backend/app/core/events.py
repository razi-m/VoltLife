from collections import deque
from fastapi import WebSocket
from typing import List
from app.core.logging import logger

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Ring buffer of the last 20 events, shared by WebSocket seed and polling GET jobs/{id} fallback
        self.ring_buffer = deque(maxlen=20)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
        
        # When a client connects, catch them up with recent events from the ring buffer
        for event in list(self.ring_buffer):
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.error(f"Failed to catch up new WebSocket client: {e}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, event: dict):
        """
        Appends event to the ring buffer and broadcasts to all active connections.
        Performs per-connection try/except to isolate failures (e.g. broken pipe).
        """
        # Append to ring buffer
        self.ring_buffer.append(event)
        
        if not self.active_connections:
            return
            
        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket connection, marking for removal: {e}")
                failed_connections.append(connection)
                
        # Clean up failed connections
        for connection in failed_connections:
            self.disconnect(connection)

manager = WebSocketManager()
