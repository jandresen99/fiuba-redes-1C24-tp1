from logging import Logger
from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWait
from lib.utils import *
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
import os
from queue  import Queue

class Client:
    def __init__(self, ip, port, type, logger: Logger, destination):
        self.ip = ip
        self.port = port
        self.server_address = None
        self.logger = logger
        self.protocol = StopAndWait((ip, port), logger, destination)

        if type == UPLOAD_TYPE or type == DOWNLOAD_TYPE:
            self.type = type
        else:
            self.logger.error(f"Error: invalid type")
    
    
    def start(self, args):
        thread = Thread(target=self.protocol.start_client, args=(self.type, args))
        thread.start()
        
        while True:
            datagram, _ = self.protocol.socket.recvfrom(BUFFER_SIZE)
            self.protocol.push(datagram)