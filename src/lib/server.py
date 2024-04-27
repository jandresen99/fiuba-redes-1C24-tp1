from socket import *
from threading import Thread
from logging import Logger
from queue import Queue
from lib.package import Package

class Server:
    def __init__(self, ip, port, logger: Logger):
        self.ip = ip
        self.port = port
        self.logger = logger

        self.clients = {}

    def start(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        
        self.logger.info("Listening on %s:%d", self.ip, self.port)
        try:
            self.handle_connections()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise e
    
    def handle_connections(self):
        while True:
            datagram, addr = self.socket.recvfrom(1024)
            port = addr[1]
            try:
                package_queue = self.clients[port]
                package_queue.put(datagram)

            except:
                package_queue = Queue()
                package_queue.put(datagram)
                self.clients[port] = package_queue
                client = Thread(target=self.handle_package, args=(package_queue,))
                client.start()
    
    def handle_package(self, queue):
        try:
            encoded_pkg = queue.get(block=True, timeout=1)
            decoded_pkg = Package.decode_pkg(encoded_pkg)
            print(decoded_pkg)
            print("Flags:", decoded_pkg.flags)
            print("Data Length:", decoded_pkg.data_length)
            print("File Name:", decoded_pkg.file_name)
            print("Seq Number:", decoded_pkg.seq_number)
            print("Ack Number:", decoded_pkg.ack_number)
            print("Data:", decoded_pkg.data)
        except Exception as e:
            self.logger.error(f"Errorrrrrrrrrr: {e}")
            raise e