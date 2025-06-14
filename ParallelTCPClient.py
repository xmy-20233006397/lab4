import socket
import threading
from queue import Queue
import os
import hashlib


class ParallelTCPClient:
