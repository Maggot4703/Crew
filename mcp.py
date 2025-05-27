import socket
import json
import threading
import time

class MCPServer:
    def __init__(self, host='127.0.0.1', port=8000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.running = False

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        # Accept client connections in a separate thread
        accept_thread = threading.Thread(target=self._accept_clients)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Keep the server running until interrupted
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def _accept_clients(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Client connected from {address}")
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                self.clients.append(client_socket)
            except Exception as e:
                if self.running:
                    print(f"Error accepting client: {e}")
    
    def _handle_client(self, client_socket, address):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    context = json.loads(data.decode('utf-8'))
                    print(f"Received context from {address}: {context}")
                    
                    # Echo back with a response
                    response = {"status": "received", "response": f"Processed request from {context.get('user', 'unknown')}"}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from {address}")
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Client {address} disconnected")
    
    def stop(self):
        self.running = False
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        # Close server socket
        self.server_socket.close()
        print("Server stopped")


class MCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            return True
        except ConnectionRefusedError:
            print(f"Error: Could not connect to server at {self.host}:{self.port}.")
            print("Make sure the server is running first (use 'python mcp_example.py server').")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_context(self, context_data):
        if not isinstance(context_data, dict):
            raise ValueError("Context data must be a dictionary")
        
        json_data = json.dumps(context_data).encode('utf-8')
        self.client_socket.send(json_data)
    
    def receive_context(self, timeout=10):
        self.client_socket.settimeout(timeout)
        try:
            data = self.client_socket.recv(4096)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except socket.timeout:
            print("Timeout waiting for response")
            return None
    
    def close(self):
        self.client_socket.close()
