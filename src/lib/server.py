from socket import *
from threading import Thread
from logging import Logger
from queue import Queue
from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWaitProtocol

class Server:
    def __init__(self, ip, port, logger: Logger):
        self.ip = ip
        self.port = port
        self.logger = logger
        
        self.clients = {} # Map (port, queue)
        self.protocols = {} # Map (port, protocol)
        
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
            package, addr = self.socket.recvfrom(1024)
            port = addr[1]
            
            if port in self.clients:
                package_queue = self.clients[port]
                package_queue.put(package)
            else:
                self.handle_new_client(port, package)
                
    def handle_new_client(self, port, datagram):
        package_queue = Queue()
        package_queue.put(datagram)
        self.clients[port] = package_queue
        client = Thread(target=self.handle_package, args=(port, package_queue))
        client.start()
    
    def handle_package(self, port, queue):
        try:
            # Recivo primer mensaje
            encoded_pkg = queue.get(block=True, timeout=1)
            decoded_pkg = Package.decode_pkg(encoded_pkg)
            # debug
            print(decoded_pkg)
            print("Flags:", decoded_pkg.flags)
            print("Data Length:", decoded_pkg.data_length)
            print("File Name:", decoded_pkg.file_name)
            print("Seq Number:", decoded_pkg.seq_number)
            print("Ack Number:", decoded_pkg.ack_number)
            print("Data:", decoded_pkg.data)
            
            if decoded_pkg.flags == SYN: # Primer mensaje    
                self.three_way_handshake(decoded_pkg, port, queue)
                # ACK back to client
                
        except Exception as e:
            self.logger.error(f"Error handling package: {e}")
            raise e
    
    def three_way_handshake(self, pkg, port, queue):
        # El primer mensaje tiene 
        if pkg.data.decode() == 'sw':
            self.protocols[port] = StopAndWaitProtocol()
            print("Cliente usa stop and wait")
        else:
            print("No se reconoció el protocolo") 
        
        #self.acknowledge_connection()
        
    #def acknowledge_connection(self):
        
        
    def stop(self):
        self.socket.close()