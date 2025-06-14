import socket
import os
import hashlib


class UDPServer:
    def __init__(self, port):
        self.server_port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', port))
        print(f"[UDP Server] Started successfully, listening on port {port}")

    def start(self):
        try:
            while True:
                data, client_addr = self.server_socket.recvfrom(1024)
                message = data.decode().strip()
                print(f"[UDP Server] Received from {client_addr}: {message}")

                if message.startswith("DOWNLOAD"):
                    self.handle_download(client_addr, message)
                elif message == "QUIT":
                    print(f"[UDP Server] Client {client_addr} requested quit")

        except KeyboardInterrupt:
            print("\n[UDP Server] Shutting down...")
        finally:
            self.server_socket.close()
