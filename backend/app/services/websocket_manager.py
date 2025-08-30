from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_subscriptions: Dict[WebSocket, List[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_subscriptions[websocket] = []
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_subscriptions:
            del self.connection_subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, topics: List[str]):
        """Subscribe to specific topics (e.g., 'mumbai', 'gujarat', 'alerts')"""
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].extend(topics)
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "topics": topics
            }))

    async def broadcast_to_topic(self, message: Dict[str, Any], topic: str):
        """Broadcast message to all connections subscribed to a specific topic"""
        disconnected = []
        
        for connection in self.active_connections:
            if connection in self.connection_subscriptions and topic in self.connection_subscriptions[connection]:
                try:
                    await connection.send_text(json.dumps({
                        "type": "topic_update",
                        "topic": topic,
                        "data": message
                    }))
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps({
                    "type": "broadcast",
                    "data": message
                }))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to a specific connection"""
        try:
            await websocket.send_text(json.dumps({
                "type": "personal",
                "data": message
            }))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get current number of active connections"""
        return len(self.active_connections)

    def get_subscription_stats(self) -> Dict[str, int]:
        """Get statistics about topic subscriptions"""
        stats = {}
        for subscriptions in self.connection_subscriptions.values():
            for topic in subscriptions:
                stats[topic] = stats.get(topic, 0) + 1
        return stats


