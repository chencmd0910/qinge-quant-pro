"""WebSocket 行情推送"""
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        data = json.dumps(message, ensure_ascii=False)
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_text(data)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


async def market_websocket(websocket: WebSocket):
    """行情WebSocket端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（订阅等）
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("action") == "subscribe":
                # TODO: 订阅指定标的行情
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "symbol": msg.get("symbol", ""),
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def push_market_data(symbol: str, data: dict):
    """推送行情数据（供其他模块调用）"""
    await manager.broadcast({
        "type": "market_data",
        "symbol": symbol,
        "data": data,
    })
