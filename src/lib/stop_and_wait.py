import logging
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
        self.ack_num = None # Se determina con el primer paquete recibida
        self.tries_send = 0
        
        self.logger = logger
        
    def start(self):
        """ Empieza a consumir paquetes"""
        while True:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)
            
            self.logger.debug(f"Client {self.addr} received: {pkg}")
         
    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
