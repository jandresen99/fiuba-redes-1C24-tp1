from socket import socket, AF_INET, SOCK_DGRAM
from queue  import Queue
from lib.package import Package
from lib.values import *
from lib.utils import *
import time # TODO: sacar esto
import os
import threading

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

        self.timer = None
        self.last_sent_pkg = None  # Almacena el último paquete enviado
        
    def start_server(self):
        """ Empieza a consumir paquetes"""
        while True:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)
            
            self.logger.info(f"New package from client {self.addr}")
            
            # Checkeo que recibí el paquete que esperaba
            if self.ack_num != -1 and pkg.seq_number != self.ack_num:
                self.handle_unordered_package(pkg.seq_number)
                continue # Dropeo el paquete y vuelvo a esperar mensajes
        
            # Si soy el primero que recibe el mensaje => ack_num es None (o podria ser -1)
            if pkg.flags == SYN: 
                self.logger.info(f"SYN from client {self.addr}")
                self.ack_num = pkg.seq_number + 1
                self.acknowledge_connection()
            
            if pkg.flags == START_TRANSFER:
                self.logger.info(f"START_TRANSFER from client {self.addr}")
                self.ack_num = pkg.seq_number + 1

                if pkg.type == UPLOAD_TYPE:
                    self.logger.info(f"UPLOAD from client {self.addr}")
                    self.receive_file(self.storage, pkg.data.decode())
                
                if pkg.type == DOWNLOAD_TYPE:
                    self.logger.info(f"DOWNLOAD from client {self.addr}")
                    self.send_file(self.storage + "/" + pkg.data.decode())
    

    def start_client(self, client_type, args):
        # Primer mensaje solo tiene el SYN en 1 y si es de tipo download o upload
        # El server contesta con un SYN 1 y el ACK
        # El cliente envía un ACK con SYN 0 y la conexión queda establecida
        handshake_pkg = Package.handshake_pkg(client_type, self)
        self.logger.info(f"Sending SYN to {self.addr}")
        self.socket.sendto(handshake_pkg, self.addr) 
        
        # Esperar respuesta
        # TODO: hay que hacer un try-catch para que no explote cuando hay un
        # timeout en el recv
        datagram = self.datagram_queue.get(block=True, timeout=1)
        received_pkg = Package.decode_pkg(datagram)
        self.logger.info(f"Received data from server: {received_pkg}")
        file_name = args.name
        self.seq_num += 1
        self.ack_num = received_pkg.ack_number + 1
        pkg = Package(
            type=client_type,   
            flags=START_TRANSFER, 
            data_length=len(file_name),
            data=file_name.encode(),
            seq_number=self.seq_num,
            ack_number=self.ack_num
        ).encode_pkg()
        
        self.logger.info("Envío el pedido al server")
        self.socket.sendto(pkg, self.addr)

        if client_type == UPLOAD_TYPE:
            file_path = args.src

            self.send_file(file_path)
        
        if client_type == DOWNLOAD_TYPE:
            destination_path = args.dst

            if not os.path.isdir(destination_path):
                os.makedirs(destination_path, exist_ok=True)
            
            self.receive_file(destination_path, file_name)


    def acknowledge_connection(self):
        self.logger.info(f"Sending SYNACK to client {self.addr}")
        pkg = Package(
            type=1,
            flags=SYN,
            data_length=0,
            data=''.encode(),
            seq_number= 0,
            ack_number=self.ack_num
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)
    

    def send_ack(self, seq_number):
        self.logger.info(f"Sending ACK {seq_number} to {self.addr}")
        pkg = Package(
            type=1,
            flags=ACK,
            data_length=0,
            data=''.encode(),
            seq_number= seq_number,
            ack_number=seq_number
        ).encode_pkg()
        
        self.socket.sendto(pkg, self.addr)

    def get_ack(self):
        datagram = self.datagram_queue.get(block=True, timeout=1)
        pkg = Package.decode_pkg(datagram)
        
        
        if pkg.flags == ACK:
            self.start_timer()  #Reinicia el timer porque recibio un ACK
            return pkg
        

    

    def handle_unordered_package(self, seq_number):
        self.logger.info(f"Unordered package from client {self.addr}")
        self.logger.info(f"Expected seq_number {self.ack_num}")
        self.logger.info(f"Got seq_number {seq_number}")
        
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
            self.logger.info(f"File size remaining: {file_size}")
            data = file.read(DATA_SIZE)
            self.seq_num += 1
            self.ack_num += 1
            data_length = len(data)

            pkg = Package(
                type=2,
                flags=NO_FLAG, 
                data_length=data_length,
                data=data,
                seq_number=self.seq_num,
                ack_number=self.ack_num
            )

            self.logger.info(f"Sending file to {self.addr}")
            self.socket.sendto(pkg.encode_pkg(), self.addr)

            # Guarda el último paquete enviado para retransmitirlo en caso de timeout
            self.last_sent_pkg = pkg.encode_pkg()   
            self.start_timer()

            file_size -= data_length

            ack_pkg = self.get_ack()

            if ack_pkg.ack_number < self.seq_num:
                self.logger.info(f"Duplicated ACK {ack_pkg.ack_number} while self.seq_num {self.seq_num} from {self.addr}")
                raise Exception
        
        self.seq_num += 1
        self.ack_num += 1

        pkg = Package(
                type=2,
                flags=FIN, 
                data_length=0,
                data=''.encode(),
                seq_number=self.seq_num,
                ack_number=0 # TODO: por ahora no le da pelota a esto
            )

        self.logger.info(f"Sending FIN to {self.addr}")
        self.timer.cancel() # Apago timer
        self.socket.sendto(pkg.encode_pkg(), self.addr)

        
    def receive_file(self, destination_path, file_name):
        keep_receiving = True
        file = open(destination_path + "/" + file_name, "wb+")

        while keep_receiving:
            datagram = self.datagram_queue.get(block=True, timeout=1)
            pkg = Package.decode_pkg(datagram)

            if pkg.flags == FIN:
                keep_receiving = False
            else:
                self.logger.info(f"Got seq_number {pkg.seq_number} from client {self.addr}")

                if self.ack_num > pkg.seq_number + 1:
                    self.logger.info(f"Wrong self.ack_num = {self.ack_num} and  pkg.seq_number + 1 = {pkg.seq_number + 1}")
                    raise Exception

                self.send_ack(pkg.seq_number)

                file.write(pkg.data)
                
                

                
        
        self.logger.info(f"File {file_name} received from client {self.addr}")

    
    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()  # Cancela el timer anterior si existe
        
        self.timer = threading.Timer(TIMEOUT_SECONDS, self.handle_timeout)
        self.timer.start()

    def handle_timeout(self):
        """ Se llama cuando se agota el temporizador (timeout) """
        if self.last_sent_pkg is not None:
            # Retransmito el último paquete 
            
            self.logger.debug("Timeout: retransmitiendo último paquete")
            self.socket.sendto(self.last_sent_pkg, self.addr)
            self.start_timer()  # Reinicia el temporizador
    
  