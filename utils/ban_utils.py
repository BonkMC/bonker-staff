import asyncio
import json
import os
import re
from dataclasses import dataclass
import aiohttp
from utils.config import AppConfig

PROXY_SERVER_ID = "d311defa-46de-4a83-bbfd-e0264897f2ce"
PANEL_URL = "https://panel.bonkmc.org"


@dataclass
class BanInfo:
    is_banned: bool
    username: str
    banned_by: str = None
    reason: str = None
    banned_on: str = None
    banned_until: str = None
    duration_remaining: str = None
    server: str = None
    scope: str = None
    ip_ban: bool = False
    silent: bool = False
    permanent: bool = False


class BanChecker:
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

    async def _get_websocket_details(self, session: aiohttp.ClientSession) -> dict:
        url = f"{self._panel_url}/api/client/servers/{self._server_id}/websocket"
        headers = self._get_headers()
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to get websocket details: {resp.status} - {text[:200]}")
            data = await resp.json()
            return data["data"]

    def _strip_ansi(self, text: str) -> str:
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_pattern.sub('', text)

    def _parse_ban_response(self, username: str, lines: list[str], complete: bool = False) -> BanInfo:
        lines = [self._strip_ansi(line) for line in lines]
        not_banned_pattern = re.compile(r"\[.*INFO.*\]:\s*Target is not banned!")
        banned_pattern = re.compile(rf"\[.*INFO.*\]:\s*Target \[{re.escape(username)}\] is banned:", re.IGNORECASE)
        
        for i, line in enumerate(lines):
            if not_banned_pattern.search(line):
                return BanInfo(is_banned=False, username=username)
            
            if banned_pattern.search(line):
                remaining_lines = lines[i+1:]
                has_ip_ban_line = any("IP ban:" in l for l in remaining_lines)
                
                if not complete and not has_ip_ban_line:
                    return None
                
                ban_info = BanInfo(is_banned=True, username=username)
                
                for detail_line in remaining_lines[:7]:
                    if "Banned by:" in detail_line:
                        ban_info.banned_by = detail_line.split("Banned by:")[-1].strip()
                    elif "Reason:" in detail_line:
                        ban_info.reason = detail_line.split("Reason:")[-1].strip()
                    elif "Banned on:" in detail_line and "server" not in detail_line.lower():
                        ban_info.banned_on = detail_line.split("Banned on:")[-1].strip()
                    elif "Banned until:" in detail_line:
                        until_part = detail_line.split("Banned until:")[-1].strip()
                        match = re.match(r"([^\(]+)\s*\(([^)]+)\)", until_part)
                        if match:
                            ban_info.banned_until = match.group(1).strip()
                            ban_info.duration_remaining = match.group(2).strip()
                        else:
                            ban_info.banned_until = until_part
                    elif "Banned on server" in detail_line:
                        server_match = re.search(r"Banned on server (\w+)", detail_line)
                        scope_match = re.search(r"server scope: (\w+)", detail_line)
                        if server_match:
                            ban_info.server = server_match.group(1)
                        if scope_match:
                            ban_info.scope = scope_match.group(1)
                    elif "IP ban:" in detail_line:
                        ban_info.ip_ban = "yes" in detail_line.lower().split("ip ban:")[-1].split(",")[0]
                        ban_info.silent = "silent: yes" in detail_line.lower()
                        ban_info.permanent = "permanent: yes" in detail_line.lower()
                
                return ban_info
        
        return None

    async def check_ban(self, username: str, timeout: float = 5.0, debug: bool = False) -> BanInfo:
        async with aiohttp.ClientSession() as session:
            ws_details = await self._get_websocket_details(session)
            ws_url = ws_details["socket"]
            token = ws_details["token"]
            
            ws_url_with_token = f"{ws_url}?token={token}"
            
            collected_lines = []
            
            ws_headers = {
                "Origin": self._panel_url
            }
            if self._cf_client_id and self._cf_client_secret:
                ws_headers["CF-Access-Client-Id"] = self._cf_client_id
                ws_headers["CF-Access-Client-Secret"] = self._cf_client_secret
            async with session.ws_connect(ws_url_with_token, headers=ws_headers) as ws:
                auth_msg = json.dumps({"event": "auth", "args": [token]})
                await ws.send_str(auth_msg)
                
                await asyncio.sleep(0.5)
                
                command_msg = json.dumps({
                    "event": "send command",
                    "args": [f"checkban {username}"]
                })
                await ws.send_str(command_msg)
                
                start_time = asyncio.get_event_loop().time()
                
                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if debug:
                                print(f"WS event: {data.get('event')} | args: {data.get('args', [])[:1]}")
                            if data.get("event") == "console output":
                                line = data.get("args", [""])[0]
                                collected_lines.append(line)
                                
                                result = self._parse_ban_response(username, collected_lines)
                                if result is not None:
                                    return result
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        if debug:
                            print(f"Exception: {e}")
                        break
            
            if debug:
                print(f"\nCollected {len(collected_lines)} lines:")
                for line in collected_lines:
                    print(f"  {repr(line)}")
            
            result = self._parse_ban_response(username, collected_lines, complete=True)
            if result:
                return result
            
            return BanInfo(is_banned=False, username=username)


async def check_player_ban(username: str) -> BanInfo:
    checker = BanChecker()
    return await checker.check_ban(username)
