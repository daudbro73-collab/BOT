from __future__ import annotations

import logging
from pathlib import Path

import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class DashboardServer:
    """aiohttp server with WebSocket broadcast for real-time dashboard."""

    def __init__(self) -> None:
        self.app = web.Application()
        self.clients: set[web.WebSocketResponse] = set()
        self.latest_data: dict = {}
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.app.router.add_get("/", self._index)
        self.app.router.add_get("/ws", self._websocket)

    async def _index(self, request: web.Request) -> web.FileResponse:
        return web.FileResponse(STATIC_DIR / "index.html")

    async def _websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)
        self.clients.add(ws)
        logger.info("WS client connected (%d total)", len(self.clients))

        # Send latest snapshot immediately
        if self.latest_data:
            await ws.send_json(self.latest_data)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self.clients.discard(ws)
            logger.info("WS client disconnected (%d total)", len(self.clients))
        return ws

    async def broadcast(self, data: dict) -> None:
        """Push data to all connected WebSocket clients."""
        self.latest_data = data
        dead: set[web.WebSocketResponse] = set()
        for ws in self.clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.clients -= dead

    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info("Dashboard server listening on http://%s:%d", host, port)
        return runner
