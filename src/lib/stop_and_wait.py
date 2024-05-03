from socket import socket, AF_INET, SOCK_DGRAM
from queue  import Queue

from lib.package import Package
from lib.values import *

class StopAndWait():
    """ Clase que encapsula toda la comunicación: recursos utilizados, estado de
        la comunicación, etc.
    """
    
    def __init__(self, addr, logger):
        # TODO: no se si se puede usar un socket concurrentemente para enviar mensajes
        # => creo uno nuevo. Puede ser que se pueda usar el mismo para todas las conexiones
        # Recursos para la comunicación
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.datagram_queue = Queue()
        self.addr = addr
        
        self.name = STOP_AND_WAIT
        
        # Contadores globales para el envío ordenado y checkeo de errores
        self.seq_num = 0
        self.ack_num = -1 # Se determina con el primer paquete recibida
        self.tries_send = 0
        
        self.logger = logger
        
    def start(self):
        """ Empieza a consumir paquetes"""
        while True:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)
            
            self.logger.debug(f"Client {self.addr} received: {pkg}")
            
            # Checkeo que recibí el paquete que esperaba
            if self.ack_num != -1 and pkg.seq_number != self.ack_num:
                self.handle_unordered_package(pkg.seq_number)
                continue # Dropeo el paquete y vuelvo a esperar mensajes
        
            # TODO: por ahora esta solo es la lógica del lado del server
            # Si soy el primero que recibe el mensaje => ack_num es None (o podria ser -1)
            if pkg.flags == SYN: 
                print("Recibí un SYN: primer mensaje del cliente")
                self.ack_num = pkg.seq_number + 1
                self.acknowledge_connection()
            
            if pkg.flags == START_TRANSFER:
                print("Recibí un start_transfer: cliente quiere transferir datos")
                self.ack_num = pkg.seq_number + 1
                self.start_data_transfer(pkg)
            
    def acknowledge_connection(self):
        print("Le mando SYNACK al cliente")
        pkg = Package(
            type=1, # TODO: creo que el type puede ser un flag y listo
            flags=SYN,
            data_length=0,
            file_name='', # TODO: sacar esto
            data=''.encode(),
            seq_number= 0,
            ack_number= self.ack_num
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)
        
    def start_data_transfer(self, pkg: Package):
        print(f"Comenzando a transferir datos con: {self.addr}")
        print(f"Me debería haber llegado tipo de transferencia y nombre de archivo")
        
        if pkg.type == UPLOAD_TYPE: # El server va a recibir datos para descargar
            # TODO: extraer el nombre de archivo y lo que sea de pkg
            self.download_file()
            
    def handle_unordered_package(self, seq_number):
        """En stop and wait el paquete se dropea y reenvio el ack"""
        print(
            f"Se esperaba recibir el paquete con seq_num {self.ack_num} "
            f"pero se recibió el paquete {seq_number}.\n"
            f"Vuelvo a enviar ACK = {self.ack_num}"
        )
        
        pkg = Package(
            type=1, # TODO: creo que el type puede ser un flag y listo
            flags=NO_FLAG,
            data_length=0,
            file_name='', # TODO: sacar esto
            data=''.encode(),
            seq_number= 0,
            ack_number= self.ack_num
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)
        
    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
        
    def download_file(self):
        # TODO: este pasa a convertirse en el loop principal. El pkg recibido
        # es el del flag START_TRANSFER y tiene que tener como datos el nombre
        # del archivo, donde lo quiere guardar etc. Eso se hace una única vez
        # acá y ya queda guardado => en ese paquete el cliente manda esa info
        # dentro de data
        
        # TODO: esta va a ser la misma función que usa el cliente cuando quiera
        # descargarse algo
        while True:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)
            
            print(f"From client {self.addr} received: {pkg.data.decode()}")
