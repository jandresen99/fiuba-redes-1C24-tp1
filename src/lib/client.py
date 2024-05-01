from logging import Logger
from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWaitProtocol
import socket

class Client:
    def __init__(self, ip, port, type, logger: Logger):
        self.ip = ip
        self.port = port
        self.server_address = None
        self.logger = logger
        self.protocol = StopAndWaitProtocol()

        if type == UPLOAD_TYPE or type == DOWNLOAD_TYPE:
            self.type = type
        else:
            self.logger.error(f"Error: invalid type")
    
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(1)

        self.handshake_to_server()
    
    def handshake_to_server(self):
        # Primer mensaje solo tiene el SYN en 1 y si es de tipo download o upload
        # El server contesta con un SYN 1 y el ACK
        # El cliente envía un ACK con SYN 0 y la conexión queda establecida
        handshake_pkg = Package.handshake_pkg(self.type, self.protocol)
        self.send(handshake_pkg)
        self.logger.info("Sent handshake to server")
        # Esperar respuesta
        # datagram, _ = self.socket.recvfrom(BUFFER_SIZE)
        # pkg = Package.decode_pkg(datagram)
        # self.logger.info(f"Received data from server: {pkg}")
        # Empezar download o upload
        
        
        
    
    def send(self, package, address=None):
        if not address:
            address = (self.ip, self.port)
        
        self.socket.sendto(package, address)
