from socket import *
from threading import Thread
from logging import Logger

from lib.rdt_pkg import RDTPackage

class Server:
    def __init__(self, ip, port, logger: Logger):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.logger = logger
        
        self.clients = set()
        
        self.logger.info("Listening on %s:%d", ip, port)

    def start(self):
        # Este thread es el que se encarga de escuchar mensajes recibidos constantemente.
        # Es el único punto de entrada de mensajes del server
        # Parece que no tiene mucho sentido crear un socket UDP por cliente, buscarle
        # un puerto a cada socket y handlear errores para eso. Suena bardo.
        # Luego cada thread por cliente procesa el mensaje recibido
        # Para ver manejo de clientes concurrentemente usando UDP:
        # https://stackoverflow.com/questions/45904197/multiple-udp-sockets-and-multiple-clients
        while True:
            datagram, addr = self.sock.recvfrom(1024)
            # TODO: acá habría que hacer el 3-way handshake?
            if addr not in self.clients:
                self.logger.info(f"New client: %s", addr)
                # Le aviso al cliente que escuché su conexión
                print(f"[NEW] Enviando ACK a ", addr)
                self.sock.sendto("ACK".encode(), addr)
                self.clients.add(addr)
            else:
                self.logger.info(f"[OLD] Client: %s", addr)
                print(f"[OLD] Enviando ACK a ", addr)
                self.sock.sendto("ACK".encode(), addr)    
                        
                client_thread = Thread(target=self._handle_client, args=(datagram, addr))   
                client_thread.start()
    
    # Por ahora solo muestra lo que recivió
    def _handle_client(self, datagram, addr):
        pkg: RDTPackage = RDTPackage.extract(datagram)
        self.logger.info("Message received from %s: %s", addr, pkg)
        return
    
    def stop(self):
        self.sock.close()