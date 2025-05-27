# Example: Using Model Context Protocol (MCP) in Python

from mcp import MCPClient, MCPServer

# Start an MCP server
def start_server():
    server = MCPServer(host='127.0.0.1', port=8000)
    print("Starting MCP server on 127.0.0.1:8000 ...")
    server.start()

# Connect as an MCP client and send/receive context
def client_example():
    client = MCPClient('127.0.0.1', 8000)
    if not client.connect():
        print("Connection failed. Exiting.")
        return
        
    print("Connected to MCP server.")
    # Send context
    data = {"user": "alice", "query": "What is MCP?"}
    client.send_context(data)
    print("Sent context:", data)
    # Receive context
    context = client.receive_context()
    print("Received context:", context)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()
    else:
        client_example()
