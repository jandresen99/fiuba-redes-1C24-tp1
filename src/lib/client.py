from logging import Logger
from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWaitProtocol
from socket import socket, AF_INET, SOCK_DGRAM

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
        self.socket = socket(AF_INET, SOCK_DGRAM)
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
        # TODO: hay que hacer un try-catch para que no explote cuando hay un
        # timeout en el recv
        datagram, _ = self.socket.recvfrom(BUFFER_SIZE)
        received_pkg = Package.decode_pkg(datagram)
        self.logger.debug(f"Received data from server: {received_pkg}")
        # Empezar download o upload
        message = 'Quiero descargar o subir algo ni idea.'.encode()
        pkg = Package(
            type=1,  
            flags=START_TRANSFER, 
            data_length=len(message),
            file_name='',
            data=message,
            seq_number=1, # TODO: un seq_number global para ir sumando
            ack_number= received_pkg.ack_number + 1
        ).encode_pkg()
        
        self.logger.debug("Envío el pedido al server")
        self.send(pkg)
        
        
        
    
    def send(self, package: bytes, address=None):
        if not address:
            address = (self.ip, self.port)
        
        self.socket.sendto(package, address)
