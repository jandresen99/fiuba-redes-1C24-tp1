from socket import socket, AF_INET, SOCK_DGRAM
from queue  import Queue
from lib.package import Package
from lib.values import *
from lib.utils import *
import time # TODO: sacar esto
import os
import threading
import time

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
        self.ack_num = 0 # Se determina con el primer paquete recibido
        
        
        self.logger = logger
        self.start_time = time.time()
        self.timer = None
        self.last_sent_pkg = None  # Almacena el último paquete enviado
        
    def start_server(self):
        """ Empieza a consumir paquetes"""
        type_of_transfer = None # TODO: usar para 
        notTransfering=True
        syn_received=False
        transfer_ack_not_received=True
        while notTransfering:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT) #CHECK
            pkg = Package.decode_pkg(datagram)
            
            # self.logger.info(f"New package from client {self.addr}")
            
            # Checkeo que recibí el paquete que esperaba
            # if self.ack_num != 0 and pkg.seq_number != self.ack_num:
            #     self.handle_unordered_package(pkg.seq_number)
            #     continue # Dropeo el paquete y vuelvo a esperar mensajes
        
            # Si soy el primero que recibe el mensaje => ack_num es None (o podria ser -1)
            if pkg.flags == SYN: 
                if syn_received==False:
                    self.logger.info(f"[{self.addr}] Received SYN")
                    #self.ack_num = pkg.seq_number + 1
                    self.send_acknowledge('SYNACK', None)
                    syn_received=True
                else:
                    self.logger.info(f"[{self.addr}] Received SYN Duplicated")
                    #self.ack_num = pkg.seq_number + 1
                    self.send_acknowledge('DUPLICATE_SYNACK', None)

            
            if pkg.flags == START_TRANSFER:
                self.logger.info(f"[{self.addr}] Received START_TRANSFER")
                self.send_acknowledge('ACK', pkg.seq_number)

                #self.ack_num = pkg.seq_number + 1

                if pkg.type == UPLOAD_TYPE:
                    self.logger.info(f"[{self.addr}] Client is UPLOADING file")
                    self.receive_file(self.storage, pkg.data.decode())
                    notTransfering = False
                    
                
                if pkg.type == DOWNLOAD_TYPE:
                    # self.logger.info(f"[{self.addr}] Client is DOWNLOADING file")
                    # self.send_file(self.storage + "/" + pkg.data.decode())
                    while transfer_ack_not_received:
                        if self.datagram_queue.empty():
                            time.sleep(1)
                        if self.datagram_queue.empty():
                            self.logger.info(f"[{self.addr}] Client is DOWNLOADING file")
                            self.send_file(self.storage + "/" + pkg.data.decode())
                            print("Termino")
                            notTransfering = False
                            break
                          
                        datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT) #CHECK
                        pkg = Package.decode_pkg(datagram)
                        if(pkg.flags==START_TRANSFER):
                            print("start duplicado")
                            self.logger.info(f"[{self.addr}] Received START_TRANSFER Duplicated")
                            #self.ack_num = pkg.seq_number + 1
                            self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
                        
                               
                    

            
    
    def start_client(self, client_type, args):
        # Primer mensaje solo tiene el SYN en 1 y si es de tipo download o upload
        # El server contesta con un SYN 1 y el ACK
        # El cliente envía un ACK con SYN 0 y la conexión queda establecida
        self.send_package(client_type, SYN, len(self.name.encode()), self.name.encode(), self.seq_num, self.ack_num)
        self.logger.info(f"[{self.addr}] Sending SYN")
        
        notTransfering = True
        file_name = args.name
        
        while notTransfering:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
            pkg = Package.decode_pkg(datagram)
            
            # Checkeo que recibí el paquete que esperaba (debug)
            # if self.ack_num != 0 and pkg.seq_number != self.ack_num:
            #     self.handle_unordered_package(pkg.seq_number)
            #     continue # Dropeo el paquete y vuelvo a esperar mensajes
        
            if pkg.flags == SYNACK:
                print("Recibi un SYNACK")
                self.send_package(client_type, START_TRANSFER, len(file_name), file_name.encode(), self.seq_num, self.ack_num)
                self.ack_num+=1       

            if pkg.flags == ACK: # El server recibió el start transfer
                self.logger.info(f"[{self.addr}] Recibí ACK del START_TRANSFER")
                self.ack_num+=1  

                if client_type == DOWNLOAD_TYPE:
                    notTransfering = False
                    self.receive_file(args.dst, file_name)
                    
                if client_type == UPLOAD_TYPE:
                    notTransfering = False
                    self.send_file(args.src)

        # get_acknowledge espera a que entre un mensaje en la queue
        # self.get_acknowledge()
        
        # #self.logger.info(f"Received data from server: {received_pkg}")
        # file_name = args.name
        # self.seq_num += 1
        # #self.ack_num = received_pkg.ack_number + 1

        # self.send_package(client_type, START_TRANSFER, len(file_name), file_name.encode(), self.seq_num, self.ack_num)       
        # self.logger.info(f"[{self.addr}] Sending START_TRANSFER")

        # self.seq_num+=1

        # if client_type == UPLOAD_TYPE:
        #     file_path = args.src
        #     self.last_sent_pkg = pkg   
        #     self.start_timer()
        #     # print("prendo timer")
        #     ack_pkg = self.get_acknowledge()
        #     self.send_file(file_path)
        
        # if client_type == DOWNLOAD_TYPE:
        #     destination_path = args.dst
        #     self.last_sent_pkg = pkg   
        #     self.start_timer()
        #     # print("prendo timer")
        #     ack_pkg = self.get_acknowledge() #Era get_ack_receiver()
            
        #     if not os.path.isdir(destination_path):
        #         os.makedirs(destination_path, exist_ok=True)
            
        #     self.receive_file(destination_path, file_name)


    def send_acknowledge(self, type, seq_number):
        if type == 'SYNACK':
            self.logger.info(f"[{self.addr}] Sending SYNACK")
            self.send_package(1, SYNACK, 0, ''.encode(), 0, self.ack_num) 
            #self.seq_num += 1
       
        if type == 'ACK':  
            self.logger.info(f"[{self.addr}] Sending ACK {seq_number}")
            self.send_package(1, ACK, 0, ''.encode(), seq_number, seq_number)       
            #self.seq_num += 1

        if type == 'DUPLICATE_ACK':
            # No aumento contadores
            self.logger.info(f"[{self.addr}] Sending ACK DUPLICATE {seq_number}")
            self.send_package(1, ACK, 0, ''.encode(), seq_number, seq_number)
            self.seq_num-=1 
            self.ack_num-=1      

        if type == 'DUPLICATE_SYNACK':
            # No aumento contadores
            self.logger.info(f"[{self.addr}] Sending SYNACK DUPLICATE {seq_number}")
            self.send_package(1, SYNACK, 0, ''.encode(), 0, self.ack_num)
            self.seq_num-=1 
            self.ack_num-=1  

    def get_acknowledge(self):
        datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
        pkg = Package.decode_pkg(datagram)
        last_pkg = Package.decode_pkg(self.last_sent_pkg)
        
        if pkg.flags == ACK:
            if pkg.ack_number == last_pkg.seq_number: #caso de ack no duplicado
                if self.timer is not None:
                    self.timer.cancel()
                    # print("apago timer")
                #self.start_timer()  #Reinicia el timer porque recibio un ACK
                self.ack_num+=1
            return pkg
        
        if pkg.flags == SYN:
            if pkg.ack_number == last_pkg.seq_number: #caso de ack no duplicado
                #("reinicio timer")
                if self.timer is not None:
                    self.timer.cancel()
                    # print("apago timer")
                #self.start_timer()  #Reinicio el timer porque recibio un ACK
                self.ack_num+=1
            return pkg
    
        if pkg.flags == SYNACK:
            if pkg.ack_number == last_pkg.seq_number: #caso de ack no duplicado
                #("reinicio timer")
                if self.timer is not None:
                    self.timer.cancel()
                    # print("apago timer")
                #self.start_timer()  #Reinicio el timer porque recibio un ACK
                self.ack_num+=1
            return pkg
        
        if pkg.flags == START_TRANSFER:
            self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
            return pkg

        
    def handle_unordered_package(self, seq_number):
        """ Puramente para debugging """
        # TODO: en selective repeat devolver ACKs independientemente del desorden
        # y guardar data en buffer
        self.logger.info(f"Unordered package from client {self.addr}")
        self.logger.info(f"Expected seq_number {self.ack_num}")
        self.logger.info(f"Got seq_number {seq_number}")                    

    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
    
    def send_file(self, file_path):
        file, file_size = prepare_file_for_transmission(file_path)

        while file_size > 0:

            self.logger.info(f"[{self.addr}] File size remaining: {file_size}")
            data = file.read(DATA_SIZE)
            #self.seq_num += 1
            data_length = len(data)
            self.send_package(2, NO_FLAG, data_length, data, self.seq_num, self.seq_num)      
            self.logger.info(f"[{self.addr}] Sending {data_length} bytes in package {self.seq_num}")

            file_size -= data_length

            _ = self.get_acknowledge()

            #if ack_pkg.ack_number == self.seq_num:
            #    self.logger.info(f"Duplicated ACK {ack_pkg.ack_number} while self.seq_num {self.seq_num} from {self.addr}")
            #    raise Exception
            
            #self.seq_num+=1
        
        #self.seq_num += 1
        self.send_package(2, FIN, 0, ''.encode(), self.seq_num, self.ack_num)      
        self.logger.info(f"[{self.addr}] File size remaining: {file_size}")
        self.logger.info(f"[{self.addr}] Sending FIN")
            # Fin del contador de tiempo
        end_time = time.time()

        # Cálculo del tiempo transcurrido
        elapsed_time = end_time - self.start_time

        # Impresión del tiempo transcurrido
        print(f"Tiempo transcurrido: {elapsed_time} segundos")
        _ = self.get_acknowledge()
        # if self.timer is not None:
        #     self.timer.cancel() # Apago timer 
            # print("apago timer")        
        
        #self.seq_num+=1
        
    def receive_file(self, destination_path, file_name):
        self.logger.info(f"[{self.addr}] Beginning to receive file")
        # Estás recibiendo un archivo => solo mandas ACKs => ya no sos el sender
        # => no te encargas del timeout
        if self.timer is not None:
            self.timer.cancel()
    
        file = open(destination_path + "/" + file_name, "wb+")

        keep_receiving = True
        fin_received=False
        while keep_receiving:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
            pkg = Package.decode_pkg(datagram)
            
            if pkg.flags == START_TRANSFER: # TODO: checkear como manejarlo dentro de start_server
                print("START TRANSFER DUPLICATED")
                self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
            
            

            elif pkg.flags == NO_FLAG: # Recibí bytes del archivo
                self.logger.info(f"[{self.addr}] Received package {pkg.seq_number}")
                print(f"[{self.addr}] SEQ_NUMBER", pkg.seq_number)
                print(f"[{self.addr}] ACK_NUMBER",self.ack_num)
                
                # TODO: está recibiendo seq = 2 y tiene ack en 0
                
                # Caso ideal: me llego el paquete en el orden correcto
                if pkg.seq_number == self.ack_num:
                    file.write(pkg.data)
                    self.send_acknowledge('ACK', pkg.seq_number)
                    
                
                # Casos de falla
                elif pkg.seq_number == (self.ack_num - 1): # Paquete duplicado (caso que ack no llega)
                    self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
                    continue

                if self.ack_num > pkg.seq_number + 1: 
                    self.logger.info(f"Wrong self.ack_num = {self.ack_num} and  pkg.seq_number + 1 = {pkg.seq_number + 1}")
                    raise Exception
                
                if pkg.seq_number == 0: #caso que recibe despues de una retransmicion
                    self.ack_num=0
            
            elif pkg.flags == FIN and fin_received==False:
                # TODO: meter un handle_fin o end o algo
                print("recibo FIN y mando ACK", pkg.seq_number)
                self.send_acknowledge('ACK', pkg.seq_number)
                fin_received = True
                
                
            elif pkg.flags == FIN and fin_received==True: 
                print("FIN DUPLICATED")
                self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
                fin_received = True
                if self.timer is not None:
                    self.timer.cancel()
                    # print("apago timer")

                keep_receiving = False #NO CONTEMPLA MAS DE UN FIN DUPLICATE


            
            
            
            
                
        self.logger.info(f"[{self.addr}] File {file_name} received")
    
    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()  # Cancela el timer anterior si existe

        self.timer = threading.Timer(PKG_TIMEOUT, self.handle_timeout)
        self.timer.start()

    def handle_timeout(self):
        """ Se llama cuando se agota el temporizador (timeout) """
        if self.last_sent_pkg is not None:
            # Retransmito el último paquete 
            
            self.logger.debug("Timeout: retransmitiendo último paquete")
            self.socket.sendto(self.last_sent_pkg, self.addr)
            print("RETRANSMITO", Package.decode_pkg(self.last_sent_pkg).flags)
            #self.seq_num=0 
            #self.ack_num=0

            self.start_timer()  # Reinicia el temporizador
            # print("prendo timer")
            # if Package.decode_pkg(self.last_sent_pkg).flags == NO_FLAG:
            #     pkg= self.get_ack()
            # elif Package.decode_pkg(self.last_sent_pkg).flags == SYN:
            #     pkg = self.get_acknowledge()
            # elif Package.decode_pkg(self.last_sent_pkg).flags == START_TRANSFER:
            #     if Package.decode_pkg(self.last_sent_pkg).type == DOWNLOAD_TYPE:
            #         pkg = self.get_acknowledge() ##Era get_ack_receiver()
            #     else:
            #         pkg= self.get_ack()
  
    def send_package(self, type, flag, data_length, data, seq_number, ack_number):
        pkg = Package(
            type=type,   
            flags=flag, 
            data_length=data_length,
            data=data,
            seq_number=seq_number,
            ack_number=ack_number
        ).encode_pkg()        
        print(type, flag, seq_number, ack_number)
        self.socket.sendto(pkg, self.addr)
        
        self.seq_num += 1
        
        # Guarda el último paquete enviado para retransmitirlo en caso de timeout
        self.last_sent_pkg = pkg
        if flag != ACK and flag != SYNACK:
            self.start_timer() # TODO: solo el sender tiene que arrancar un timer
        else:
            self.ack_num += 1