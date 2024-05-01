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
        # TODO: creo que la key de los maps debería ser (ip, port). Igual funca
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
                self.handle_new_client(addr, package)
                
    def handle_new_client(self, addr, datagram):
        port = addr[1]
        package_queue = Queue()
        package_queue.put(datagram)
        self.clients[port] = package_queue
        client = Thread(target=self.handle_package, args=(addr, package_queue))
        client.start()
    
    def handle_package(self, addr, queue):
        try:
            # Recivo primer mensaje
            encoded_pkg = queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(encoded_pkg)
            
            self.logger.debug(f"Arrived: {pkg}")
            
            if pkg.flags == SYN: # Es el primer mensaje del cliente  
                self.three_way_handshake(pkg, addr, queue)
                
        except Exception as e:
            self.logger.error(f"Error handling package: {e}")
            raise e
    
    def three_way_handshake(self, pkg: Package, addr, queue):
        port = addr[1]
        # El primer mensaje tiene el protocolo a usar 
        if pkg.data.decode() == 'sw':
            self.protocols[port] = StopAndWaitProtocol()
            print("Cliente usa stop and wait")
        else:
            print("No se reconoció el protocolo") 
        
        self.acknowledge_connection(addr, pkg)
        
    def acknowledge_connection(self, addr, client_pkg: Package):
        """Esta función reserva los recursos que va a utilizar en la comunicación
           con el cliente y envía el paquete ACK al cliente"""
           
        # Este socket se usa exclusivamente para ENVIAR mensajes al cliente.
        client_socket = socket(AF_INET, SOCK_DGRAM)
        # TODO: hay que guardar en algun lado el socket del cliente
        pkg = Package(
            type=1,  
            flags=SYN, 
            data_length=0,
            file_name='',
            data=''.encode(),
            seq_number= 0,
            ack_number= client_pkg.ack_number + 1
        )
        
        client_socket.sendto(pkg.encode_pkg(), addr)
        
    def stop(self):
        self.socket.close()