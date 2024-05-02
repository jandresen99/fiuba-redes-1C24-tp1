from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from logging import Logger
from queue import Queue

from lib.package import Package
from lib.values import *
from lib.stop_and_wait import StopAndWait

class Server:
    """Se encarga de recibir todos los mensajes, instanciar nuevos clientes, 
       manejo de threads, pushear los mensajes a los clientes indicados (multiplexar)
       manejo de archivos y cerrar todo de forma ordenada.       
    """
    
    def __init__(self, ip, port, logger: Logger):
        self.ip = ip
        self.port = port
        self.logger = logger
        # TODO: hacer clase ClientServer o Connection o algo así que guarde queue, protocol y socket
        self.clients = {} # Map (addr, queue)
        self.protocols = {} # Map (addr, protocol)
        self.clients_sockets = {} # Map (addr, socket)
        
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
            print("Server esperando paquete")
            datagram, addr = self.socket.recvfrom(1024)
            
            self.logger.debug(f"Arrived: {Package.decode_pkg(datagram)}, from {addr}")
            # Nueva versión
            if addr in self.clients:
                self.clients[addr].push(datagram)
            else:
                new_client = StopAndWait(addr, self.logger)
                self.clients[addr] = new_client
                
                new_client.push(datagram)
                thread = Thread(target=self.start_new_client, args=(addr))
                self.threads[addr] = thread
                
            # Vieja versión
            # if addr in self.clients:
            #     package_queue = self.clients[addr]
            #     package_queue.put(datagram)
            # else:
            #     self.handle_new_client(addr, datagram)
                
    def start_new_client(self, addr):
        """Solo para el tema de los threads"""
        self.clients[addr].start()
                
    def handle_new_client(self, addr, datagram):
        # TODO: acá es donde vas a instanciar un Stop&Wait o SelectiveRepeat
        # TODO: queda medio rara esta parte
        datagram_queue = Queue()
        datagram_queue.put(datagram)
        self.clients[addr] = datagram_queue
        
        client = Thread(target=self.begin_connection, args=(addr, datagram_queue))
        client.start()
    
    def begin_connection(self, addr, queue):
        data_transfer_started = False
        
        while not data_transfer_started:
            try:
                encoded_pkg = queue.get(block=True, timeout=1)
                pkg = Package.decode_pkg(encoded_pkg)
                                        
                if pkg.flags == SYN: # Es el primer mensaje del cliente  
                    self.three_way_handshake(pkg, addr, queue)
                elif pkg.flags == START_TRANSFER:
                    data_transfer_started = True
                    self.start_data_transfer(addr, pkg)
                    
            except Exception as e:
                self.logger.error(f"Error handling package: {e}")
                raise e
    
    def three_way_handshake(self, pkg: Package, addr, queue):
        # El primer mensaje tiene el protocolo a usar 
        if pkg.data.decode() == 'sw':
            self.protocols[addr] = StopAndWait(addr, self.logger)
            print("Cliente usa stop and wait")
        else:
            raise ValueError("No se reconoció el protocolo") 
        
        self.acknowledge_connection(addr, pkg)
        
    def acknowledge_connection(self, addr, client_pkg: Package):
        """Esta función reserva los recursos que va a utilizar en la comunicación
           con el cliente y envía el paquete ACK al cliente."""
           
        # Este socket se usa exclusivamente para ENVIAR mensajes al cliente.
        client_socket = socket(AF_INET, SOCK_DGRAM)
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
        self.clients_sockets[addr[1]] = client_socket
        
    def start_data_transfer(self, addr, pkg: Package):
        self.logger.debug(f"Comenzando a transferir datos con: {addr}")
        self.logger.debug(f"Me debería haber llegado tipo de transferencia y nombre de archivo")
        # TODO: fijarse si es un download o upload y hacer el loop
        # TODO: acá es donde entra en un while "se sigue transfiriendo data",
        # escucho de la queue y voy procesando.
        # TODO: esta parte va a depender del protocolo que eligió el cliente
        # TODO: hacer un catch para el queue.Empty. Tenés que contar la cantidad
        # de timeouts y dar de baja sino
        
    def stop(self):
        self.socket.close()

# El server solo se encarga de recibir mensajes, crear conexiones con clientes y pushear
# los mensajes en las queues de cada uno. Nada de handshake y eso en el server
# Esas conexiones las encapsulamos en clases Protocolo.