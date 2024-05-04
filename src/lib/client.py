from logging import Logger
from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWait
from socket import socket, AF_INET, SOCK_DGRAM

import time # TODO: sacar esto
import os

class Client:
    def __init__(self, ip, port, type, logger: Logger):
        self.ip = ip
        self.port = port
        self.server_address = None
        self.logger = logger
        self.protocol = StopAndWait((ip, port), logger)

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

    def upload(self, file_path, file_name):
        print("Preparando el envio del archivo...")
        print("File Path:", file_path)
        print("File Path:", file_name)

        print("Comprobando que el archivo exista...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo '{file_path}' no existe")
        else:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError(f"El archivo tamaño del archivo '{file_path}' es cero")

                
        file = open(file_path, "rb") # rb es para leer en binario

        data = file.read()

        seq_number = 2
        # Es lo mismo que hace el servidor pero del lado del cliente
        # TODO: por ahora esta función solo va a enviar paquetes a mil sin nada adentro
        time.sleep(0.75)
            
        pkg = Package(
            type=1,  
            flags=NO_FLAG, 
            data_length=len(data),
            file_name=file_name,
            data=data,
            seq_number=seq_number,
            ack_number=0 # TODO: por ahora no le da pelota a esto
        ).encode_pkg()
        
        self.send(pkg)         
        
    def send(self, package: bytes, address=None):
        if not address:
            address = (self.ip, self.port)
        
        self.socket.sendto(package, address)
