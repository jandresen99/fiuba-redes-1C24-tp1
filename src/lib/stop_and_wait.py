from socket import socket, AF_INET, SOCK_DGRAM
from queue  import Queue
from lib.package import Package
from lib.values import *
from lib.utils import *
import time # TODO: sacar esto
import os

class StopAndWait():
    """ Clase que encapsula toda la comunicación: recursos utilizados, estado de
        la comunicación, etc.
    """
    
    def __init__(self, addr, logger, storage):
        # TODO: no se si se puede usar un socket concurrentemente para enviar mensajes
        # => creo uno nuevo. Puede ser que se pueda usar el mismo para todas las conexiones
        # Recursos para la comunicación
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.datagram_queue = Queue()
        self.addr = addr
        self.storage = storage
        
        self.name = STOP_AND_WAIT
        
        # Contadores globales para el envío ordenado y checkeo de errores
        self.seq_num = 0
        self.ack_num = -1 # Se determina con el primer paquete recibida
        self.tries_send = 0
        
        self.logger = logger
        
    def start_server(self):
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

                if pkg.type == UPLOAD_TYPE:
                    self.receive_file(self.storage, pkg.data.decode())
                
                if pkg.type == DOWNLOAD_TYPE:
                    self.send_file(self.storage + "/" + pkg.data.decode())
    

    def start_client(self, client_type, args):
        # Primer mensaje solo tiene el SYN en 1 y si es de tipo download o upload
        # El server contesta con un SYN 1 y el ACK
        # El cliente envía un ACK con SYN 0 y la conexión queda establecida
        handshake_pkg = Package.handshake_pkg(client_type, self)
        self.socket.sendto(handshake_pkg, self.addr) 
        
        # Esperar respuesta
        # TODO: hay que hacer un try-catch para que no explote cuando hay un
        # timeout en el recv
        datagram, _ = self.socket.recvfrom(BUFFER_SIZE)
        received_pkg = Package.decode_pkg(datagram)
        self.logger.debug(f"Received data from server: {received_pkg}")
        file_name = args.name
        self.seq_num += 1
        pkg = Package(
            type=client_type,   
            flags=START_TRANSFER, 
            data_length=len(file_name),
            data=file_name.encode(),
            seq_number=self.seq_num,
            ack_number= received_pkg.ack_number + 1
        ).encode_pkg()
        
        self.logger.debug("Envío el pedido al server")
        self.socket.sendto(pkg, self.addr)

        if client_type == UPLOAD_TYPE:
            file_path = args.src

            self.send_file(file_path)
        
        if client_type == DOWNLOAD_TYPE:
            destination_path = args.dst

            if not os.path.isdir(destination_path):
                os.makedirs(destination_path, exist_ok=True)
            
            #while True:
            datagram, _ = self.socket.recvfrom(BUFFER_SIZE)
            self.push(datagram)
            self.receive_file(destination_path, file_name)

            
    def acknowledge_connection(self):
        print("Le mando SYNACK al cliente")
        pkg = Package(
            type=1,
            flags=SYN,
            data_length=0,
            data=''.encode(),
            seq_number= 0,
            ack_number= self.ack_num
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)
    

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
            data=''.encode(),
            seq_number= 0,
            ack_number= self.ack_num
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)
        

    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
    

    def send_file(self, file_path):
        file, file_size = prepare_file_for_transmission(file_path)

        while file_size > 0:
            print("File size remaining:", file_size)
            data = file.read(DATA_SIZE)
            self.seq_num += 1
            data_length = len(data)

            pkg = Package(
                type=2,
                flags=NO_FLAG, 
                data_length=data_length,
                data=data,
                seq_number=self.seq_num,
                ack_number=0 # TODO: por ahora no le da pelota a esto
            )

            self.socket.sendto(pkg.encode_pkg(), self.addr)

            file_size -= data_length
        
        self.seq_num += 1

        pkg = Package(
                type=2,
                flags=FIN, 
                data_length=0,
                data=''.encode(),
                seq_number=self.seq_num,
                ack_number=0 # TODO: por ahora no le da pelota a esto
            )

        self.socket.sendto(pkg.encode_pkg(), self.addr)

        print("Mando FIN")

        
    def receive_file(self, destination_path, file_name):
        keep_receiving = True
        file = open(destination_path + "/" + file_name, "wb+")

        while keep_receiving:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)

            if pkg.flags == FIN:
                keep_receiving = False
            else:
                print(f"From client {self.addr} received package # {pkg.seq_number}")

                # TODO: Chequear orden del paquete

                file.write(pkg.data)
        
        print("Archivo recibido!")