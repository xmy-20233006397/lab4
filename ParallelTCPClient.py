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
