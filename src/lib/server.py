from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from logging import Logger
import queue
import os

from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWait
from lib.selective_repeat import SelectiveRepeat

import random # TODO: borrar esto

class Server:
    """Se encarga de recibir todos los mensajes, instanciar nuevos clientes, 
       manejo de threads, pushear los mensajes a los clientes indicados (multiplexar)
       manejo de archivos y cerrar todo de forma ordenada.       
    """
    
    def __init__(self, ip, port, logger: Logger, storage):
        self.ip = ip
        self.port = port
        self.logger = logger
        self.storage = storage

        if not os.path.isdir(self.storage):
            os.makedirs(self.storage, exist_ok=True)
        
        self.clients = {} # Map (addr, Protocol)        
        self.threads = {} # Map (addr, thread)
        
    def start(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.logger.info("Listening on %s:%d", self.ip, self.port)
        
        try:
            self.listen_for_packets()
            
        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise e
    
    def listen_for_packets(self):
        """Único punto de entrada del server. Recibe conexiones nuevas y 
           dirige los mensajes a los clientes correspondientes"""
           
        while True:
            datagram, addr = self.socket.recvfrom(BUFFER_SIZE)
            
            ####################################################################
            # TODO: borrar esto
            # Dropeo el 50% de los paquetes para testear
            rand_num = random.random() # Entre 0 y 1
            if rand_num < 0.5:
                num_package = Package.decode_pkg(datagram).seq_number
                print(f"\n[DROP] Se perdió el package {num_package} proveniente de {addr}")
                print(f"Flags: {Package.decode_pkg(datagram).flags}\n")
                continue
            ####################################################################
    
            if addr in self.clients:
                self.logger.info(f"Old client: {addr}")
                self.clients[addr].push(datagram)
            else:
                self.handle_new_client(addr, datagram)
                
                
    def handle_new_client(self, addr, datagram):
        # El primer mensaje recibido siempre tiene el nombre del protocolo a usar
        protocol_name = (Package.decode_pkg(datagram).data).decode('utf-8')
        
        if protocol_name == STOP_AND_WAIT:
            self.logger.info(f"[NEW CLIENT] {addr} using 'Stop & Wait' protocol")
            new_client = StopAndWait(addr, self.logger, self.storage)
        elif protocol_name == SELECTIVE_REPEAT:
            self.logger.info(f"[NEW CLIENT] {addr} using 'Selective Repeat' protocol")
            new_client = SelectiveRepeat(addr, self.logger, self.storage)
        else:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        
        new_client.push(datagram)
        self.clients[addr] = new_client
        # Inicializo el thread del cliente
        thread = Thread(target=self.start_new_client, args=(addr,))
        self.threads[addr] = thread
        thread.start()
        
                
    def start_new_client(self, addr):
        """Solo para definir una función para que empiezen los threads los threads"""
        try:
            self.clients[addr].start_server()
        except queue.Empty: # TODO: deberias lanzar una excepcion cuando se pasan los tries
            self.logger.info(f"[{addr}] Lost connection with client")
        
    def stop(self):
        self.socket.close()
