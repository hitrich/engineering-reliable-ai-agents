"""Bounded MCP 2025-11-25 stdio example. Fixed local Cedar read principal.
Not an HTTP server, general-purpose MCP SDK, or remote identity implementation.
"""
import json
import sys
from northstar import Store, Principal, BoundaryError, dispatch, tool_specs, encoded


def main():
    store = Store(); store.seed()
    principal = Principal("Cedar", "local-mcp-reader", frozenset({"read"}))
    specs = [{"name": t["name"], "description": t["description"],
              "inputSchema": t["input_schema"],
              "annotations": {"readOnlyHint": True, "openWorldHint": False}}
             for t in tool_specs() if t["name"].startswith("read_")]
    initialized, ready = False, False
    while True:
        raw = sys.stdin.buffer.readline(65537)
        if not raw:
            break
        if len(raw) > 65536:
            print("Message exceeds local size limit", file=sys.stderr)
            break
        request_id = None
        try:
            request = json.loads(raw)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
                raise ValueError("Invalid request")
            method = request["method"]
            request_id = request.get("id")
            if "id" not in request:
                if method == "notifications/initialized" and initialized:
                    ready = True
                continue
            if type(request_id) not in (str, int):
                raise ValueError("Invalid request ID")
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("Invalid params")
            if method == "initialize" and not initialized:
                if not all(key in params for key in ("protocolVersion", "capabilities", "clientInfo")):
                    raise ValueError("Missing initialization fields")
                initialized = True
                result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}},
                          "serverInfo": {"name": "northstar-local-reads", "version": "1.0.0"}}
            elif method == "ping":
                result = {}
            elif not ready:
                raise ValueError("Initialize before using tools")
            elif method == "tools/list":
                result = {"tools": specs}
            elif method == "tools/call":
                if params.get("name") not in {t["name"] for t in specs}:
                    raise ValueError("Unknown tool")
                try:
                    value = dispatch(store, principal, params["name"], params.get("arguments", {}))
                    result = {"content": [{"type": "text", "text": encoded(value)}],
                              "structuredContent": value, "isError": False}
                except BoundaryError as error:
                    result = {"content": [{"type": "text", "text": str(error)}], "isError": True}
            else:
                print(encoded({"jsonrpc": "2.0", "id": request_id,
                               "error": {"code": -32601, "message": "Method not found"}}), flush=True)
                continue
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        except (ValueError, TypeError):
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid request or parameters"}}
        print(encoded(response), flush=True)


if __name__ == "__main__":
    main()
