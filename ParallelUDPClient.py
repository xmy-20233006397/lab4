import socket
import threading
from queue import Queue
import os
import hashlib


class ParallelUDPClient:
    def __init__(self, host, port, file_list, max_threads=4):
        self.server_host = host
        self.server_port = port
        self.file_list = file_list
        self.max_threads = max_threads
        self.file_queue = Queue()
        self.lock = threading.Lock()
        self.max_retries = 3
        self.timeout = 5
        self.buffer_size = 4096
    def run(self):
        try:
            with open(self.file_list, 'r', encoding='utf-8') as f:
                filenames = [line.strip() for line in f if line.strip()]
            for filename in filenames:
                self.file_queue.put(filename)
            threads = []
            for _ in range(min(self.max_threads, len(filenames))):
                t = threading.Thread(target=self.worker)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
        except FileNotFoundError:
            print(f"[UDP Client] Error: File list {self.file_list} does not exist")
        except Exception as e:
            print(f"[UDP Client] Error: {e}")

    def worker(self):
        # Worker thread function
        while not self.file_queue.empty():
            filename = self.file_queue.get()  # Get filename from queue
            try:
                self.download_file(filename)  # Download file
            finally:
                self.file_queue.task_done()  # Mark task as completed

    def download_file(self, filename):
        # Download single file
        with self.lock:
            print(f"[UDP Client] Starting download: {filename}")
        # Create UDP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(self.timeout)  # Set timeout
        try:
            # Send download request
            request = f"DOWNLOAD {filename}"
            client_socket.sendto(request.encode(), (self.server_host, self.server_port))
            # Receive initial response
            response, _ = client_socket.recvfrom(1024)
            response = response.decode()
            if response.startswith("ERR"):  # Error handling
                with self.lock:
                    print(f"[UDP Client] Download failed for {filename}: {response}")
                return
            # Parse response information
            parts = response.split()
            file_size = int(parts[parts.index("SIZE") + 1])  # File size
            checksum = parts[parts.index("CHECKSUM") + 1]
            with self.lock:
                print(f"[UDP Client] Receiving file {filename} (size: {file_size} bytes)")
            temp_filename = filename + ".download"  # Temporary filename
            md5 = hashlib.md5()  # Hash object
            received_size = 0
            expected_sequence = 0
            received_chunks = {}  # Out-of-order packet buffer
            with open(temp_filename, 'wb') as file:
                while received_size < file_size:
                    try:
                        # Receive packet
                        data, _ = client_socket.recvfrom(self.buffer_size + 4)
                        if data == b'END':
                            break
                        # Parse sequence number and content
                        sequence = int.from_bytes(data[:4], 'big')
                        chunk = data[4:]  # Actual data content
                        if sequence == expected_sequence:
                            file.write(chunk)  # Write to file
                            md5.update(chunk)  # Update hash
                            received_size += len(chunk)
                            expected_sequence += 1
                            # Process buffered subsequent packets
                            while expected_sequence in received_chunks:
                                chunk = received_chunks.pop(expected_sequence)
                                file.write(chunk)
                                md5.update(chunk)
                                received_size += len(chunk)
                                expected_sequence += 1
                            # Print progress
                            with self.lock:
                                print(
                                    f"\r[Progress {filename}] {received_size}/{file_size} ({received_size / file_size:.1%})",
                                    end='', flush=True)
                        else:
                            received_chunks[sequence] = chunk
                    except socket.timeout:  # Timeout handling
                        with self.lock:
                            print(f"\n[UDP Client] Timeout receiving {filename}")
                        break
            if received_size == file_size and md5.hexdigest() == checksum:
                # Rename temporary file
                if os.path.exists(filename):
                    os.replace(temp_filename, filename)
                else:
                    os.rename(temp_filename, filename)
                with self.lock:
                    print(f"\n[UDP Client] File {filename} downloaded and verified successfully")
            else:
                with self.lock:
                    print(f"\n[UDP Client] File {filename} incomplete or checksum mismatch")
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)  # Delete temporary file
        except Exception as e:  # Exception handling
            with self.lock:
                print(f"\n[UDP Client] Error downloading {filename}: {e}")
        finally:
            client_socket.close()  # Close socket


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python3 UDPClient.py <host> <port> <file_list> [threads]")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    file_list = sys.argv[3]
    max_threads = int(sys.argv[4]) if len(sys.argv) == 5 else 4
    client = ParallelUDPClient(host, port, file_list, max_threads)
    client.run()
