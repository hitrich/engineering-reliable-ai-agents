"""One bounded integration check over the real stdio transport."""
import json
import select
import subprocess
import sys
from pathlib import Path


def main():
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("mcp_read_server.py"))],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def send(message, response=True):
        process.stdin.write((json.dumps(message) + "\n").encode()); process.stdin.flush()
        if response:
            assert select.select([process.stdout], [], [], 5)[0], "server timeout"
            return json.loads(process.stdout.readline())
    try:
        initial = send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "book-check", "version": "1.0"}}})
        assert initial["result"]["protocolVersion"] == "2025-11-25"
        send({"jsonrpc": "2.0", "method": "notifications/initialized"}, False)
        listed = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        assert {t["name"] for t in listed["result"]["tools"]} == {"read_ticket", "read_account", "read_export", "read_policy"}
        read = send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "read_ticket", "arguments": {"ticket_id": "T-104"}}})
        assert read["result"]["structuredContent"]["tenant"] == "Cedar"
        extra = send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "read_ticket", "arguments": {"ticket_id": "T-104", "tenant": "Juniper"}}})
        assert extra["result"]["isError"] is True
        denied = send({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "propose_update", "arguments": {}}})
        assert denied["error"]["code"] == -32602
        process.stdin.close(); process.wait(timeout=5)
        assert process.returncode == 0
        print("MCP stdio integration passed: initialize, discover, authorized read, extra-field denial, write-tool exclusion.")
    finally:
        if process.poll() is None:
            process.kill(); process.wait()


if __name__ == "__main__":
    main()
