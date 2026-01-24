import sys
import requests
import uuid
import json
from pathlib import Path


def _append_root_path():
    # find the .env.example file in a parent directory and return that directory
    def _get_root_path() -> Path:
        current_path = Path(__file__).resolve()
        for parent in current_path.parents:
            if (parent / ".env.example").exists():
                return parent
        return current_path.parent

    sys.path.insert(0, str(_get_root_path()))


_append_root_path()

from api.lib.descope.auth_config import get_settings  # noqa: E402


def send_rpc(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }
    setting = get_settings()
    server_url = setting.MCP_SERVER_URL
    resp = requests.post(server_url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data["result"]


def initialize():
    return send_rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",  # or whatever version your server supports
            "capabilities": {},
        },
    )


def list_tools():
    return send_rpc("tools/list")


def call_tool(name, arguments):
    return send_rpc(
        "tools/call",
        {
            "name": name,
            "arguments": arguments,
        },
    )


if __name__ == "__main__":
    # 1. Initialize session
    init_result = initialize()
    print("Initialized:", json.dumps(init_result, indent=2))

    # 2. Discover tools
    tools_result = list_tools()
    print("Tools:", json.dumps(tools_result, indent=2))

    # Pick first tool just as a demo
    tools = tools_result.get("tools", [])
    if not tools:
        print("No tools exposed by server.")
        exit(0)

    first_tool = tools[0]
    tool_name = first_tool["name"]
    print(f"\nCalling tool: {tool_name}")

    # 3. Call tool with dummy args (adapt to your schema)
    # Here we just send an empty object; replace with real arguments.
    call_result = call_tool(tool_name, {})
    print("Tool result:", json.dumps(call_result, indent=2))
