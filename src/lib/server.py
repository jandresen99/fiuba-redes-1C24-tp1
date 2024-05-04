from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from logging import Logger
import queue
import os

from lib.values import *
from lib.stop_and_wait import StopAndWait

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
            datagram, addr = self.socket.recvfrom(1024)
            
            # self.logger.debug(f"Arrived: {Package.decode_pkg(datagram)}, from {addr}")

            print("Clients:", self.clients)
            
            if addr in self.clients:
                self.clients[addr].push(datagram)
            else:
                print("Nuevo cliente")
                # TODO: checkear si es stop and wait o SelectiveRepeat
                new_client = StopAndWait(addr, self.logger, self.storage)
                new_client.push(datagram)
                self.clients[addr] = new_client
                
                thread = Thread(target=self.start_new_client, args=(addr,))
                self.threads[addr] = thread
                thread.start()
                
    def start_new_client(self, addr):
        """Solo para definir una función para que empiezen los threads los threads"""
        try:
            self.clients[addr].start()
        except queue.Empty: # TODO: deberias lanzar una excepcion cuando se pasan los tries
            print(f"Se perdió la conexión con el cliente {addr}")
        
    def stop(self):
        self.socket.close()
