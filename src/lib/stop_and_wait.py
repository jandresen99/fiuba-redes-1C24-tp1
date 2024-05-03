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
         
            # TODO: por ahora esta solo es la lógica del lado del server
            # Si soy el primero que recibe el mensaje => ack_num es None (o podria ser -1)
            if pkg.flags == SYN: 
                print("Recibí un SYN: primer mensaje del cliente")
                self.ack_num = pkg.seq_number + 1
                self.acknowledge_connection()
            
            if pkg.flags == START_TRANSFER:
                print("Recibí un start_transfer: cliente quiere transferir datos")
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
        # self.logger.debug(f"Comenzando a transferir datos con: {self.addr}")
        # self.logger.debug(f"Me debería haber llegado tipo de transferencia y nombre de archivo")
        # TODO: fijarse si es un download o upload y hacer el loop
        # TODO: acá es donde entra en un while "se sigue transfiriendo data",
        # escucho de la queue y voy procesando.
        # TODO: esta parte va a depender del protocolo que eligió el cliente
        # TODO: hacer un catch para el queue.Empty. Tenés que contar la cantidad
        # de timeouts y dar de baja sino
            
    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
