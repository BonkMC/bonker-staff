import asyncio
import json
import os
from dataclasses import dataclass
import aiohttp
from utils.config import AppConfig

PROXY_SERVER_ID = "d311defa-46de-4a83-bbfd-e0264897f2ce"
PANEL_URL = "https://panel.bonkmc.org"


@dataclass
class ServerStatus:
    online: bool
    state: str = None


class ServerConnection:
    def __init__(self):
        config = AppConfig(use_updated_system=True)
        self._api_key = config.get_bonk_panel_api_key()
        self._panel_url = PANEL_URL
        self._server_id = PROXY_SERVER_ID
        self._cf_client_id = os.getenv("CF_ACCESS_CLIENT_ID")
        self._cf_client_secret = os.getenv("CF_ACCESS_CLIENT_SECRET")

    def _get_headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self._cf_client_id and self._cf_client_secret:
            headers["CF-Access-Client-Id"] = self._cf_client_id
            headers["CF-Access-Client-Secret"] = self._cf_client_secret
        return headers

    def _get_ws_headers(self) -> dict:
        headers = {"Origin": self._panel_url}
        if self._cf_client_id and self._cf_client_secret:
            headers["CF-Access-Client-Id"] = self._cf_client_id
            headers["CF-Access-Client-Secret"] = self._cf_client_secret
        return headers

    async def _get_websocket_details(self, session: aiohttp.ClientSession) -> dict:
        url = f"{self._panel_url}/api/client/servers/{self._server_id}/websocket"
        headers = self._get_headers()
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to get websocket details: {resp.status} - {text[:200]}")
            data = await resp.json()
            return data["data"]

    async def check_server_status(self) -> ServerStatus:
        async with aiohttp.ClientSession() as session:
            try:
                ws_details = await self._get_websocket_details(session)
                ws_url = ws_details["socket"]
                token = ws_details["token"]
                ws_url_with_token = f"{ws_url}?token={token}"

                async with session.ws_connect(ws_url_with_token, headers=self._get_ws_headers()) as ws:
                    auth_msg = json.dumps({"event": "auth", "args": [token]})
                    await ws.send_str(auth_msg)

                    start_time = asyncio.get_event_loop().time()
                    while (asyncio.get_event_loop().time() - start_time) < 3.0:
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("event") == "status":
                                    state = data.get("args", [""])[0]
                                    return ServerStatus(online=(state == "running"), state=state)
                        except asyncio.TimeoutError:
                            continue

                return ServerStatus(online=False, state="unknown")
            except Exception:
                return ServerStatus(online=False, state="error")

    async def send_command(self, command: str) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                ws_details = await self._get_websocket_details(session)
                ws_url = ws_details["socket"]
                token = ws_details["token"]
                ws_url_with_token = f"{ws_url}?token={token}"

                async with session.ws_connect(ws_url_with_token, headers=self._get_ws_headers()) as ws:
                    auth_msg = json.dumps({"event": "auth", "args": [token]})
                    await ws.send_str(auth_msg)

                    await asyncio.sleep(0.3)

                    command_msg = json.dumps({"event": "send command", "args": [command]})
                    await ws.send_str(command_msg)

                    await asyncio.sleep(0.2)

                return True
            except Exception:
                return False

    async def send_command_with_response(self, command: str, timeout: float = 3.0) -> list[str]:
        import re
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        
        async with aiohttp.ClientSession() as session:
            try:
                ws_details = await self._get_websocket_details(session)
                ws_url = ws_details["socket"]
                token = ws_details["token"]
                ws_url_with_token = f"{ws_url}?token={token}"
                
                collected_lines = []

                async with session.ws_connect(ws_url_with_token, headers=self._get_ws_headers()) as ws:
                    auth_msg = json.dumps({"event": "auth", "args": [token]})
                    await ws.send_str(auth_msg)

                    await asyncio.sleep(0.3)

                    command_msg = json.dumps({"event": "send command", "args": [command]})
                    await ws.send_str(command_msg)

                    start_time = asyncio.get_event_loop().time()
                    while (asyncio.get_event_loop().time() - start_time) < timeout:
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("event") == "console output":
                                    line = data.get("args", [""])[0]
                                    line = ansi_pattern.sub('', line)
                                    collected_lines.append(line)
                        except asyncio.TimeoutError:
                            continue

                return collected_lines
            except Exception:
                return []


async def is_server_online() -> bool:
    conn = ServerConnection()
    status = await conn.check_server_status()
    return status.online


async def send_server_command(command: str) -> bool:
    conn = ServerConnection()
    return await conn.send_command(command)


async def send_command_with_response(command: str, timeout: float = 3.0) -> list[str]:
    conn = ServerConnection()
    return await conn.send_command_with_response(command, timeout)
