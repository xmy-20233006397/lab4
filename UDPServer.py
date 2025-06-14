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

    def handle_download(self, client_addr, message):
        # Handle file download request
        try:
            filename = message.split()[1]  # Parse filename
            if os.path.exists(filename):  # Check if file exists
                file_size = os.path.getsize(filename)  # Get file size
                md5 = hashlib.md5()  # Create MD5 hash object
                with open(filename, 'rb') as f:
                    while chunk := f.read(8192):  # Read file in chunks
                        md5.update(chunk)  # Update hash
                checksum = md5.hexdigest()  # Calculate checksum
                # Send file info response
                response = f"OK {filename} SIZE {file_size} CHECKSUM {checksum}"
                self.server_socket.sendto(response.encode(), client_addr)
                print(f"[UDP Server] Sent file info to {client_addr}")
                # Send file content in chunks
                with open(filename, 'rb') as file:
                    sequence = 0  # Initialize sequence number
                    while chunk := file.read(4096):  # Read 4096 bytes each time
                        # Build packet: 4-byte sequence number + data chunk
                        packet = sequence.to_bytes(4, 'big') + chunk
                        self.server_socket.sendto(packet, client_addr)
                        sequence += 1  # Increment sequence number
                # Send end-of-transmission marker
                self.server_socket.sendto(b'END', client_addr)
                print(f"[UDP Server] File {filename} transfer completed")
            else:
                # File not found response
                response = f"ERR {filename} NOT_FOUND"
                self.server_socket.sendto(response.encode(), client_addr)
                print(f"[UDP Server] File {filename} does not exist")
        except IndexError:
            print(f"[UDP Server] Invalid DOWNLOAD message format: {message}")
            response = "ERR INVALID_FORMAT"  # Format error response
            self.server_socket.sendto(response.encode(), client_addr)
        except Exception as e:
            print(f"[UDP Server] Error handling download request: {e}")
            response = "ERR INTERNAL_ERROR"  # Internal error response
            self.server_socket.sendto(response.encode(), client_addr)
