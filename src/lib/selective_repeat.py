from socket import socket, AF_INET, SOCK_DGRAM
from queue  import Queue
from lib.package import Package
from lib.values import *
from lib.utils import *
import threading

class SelectiveRepeat():
    """ Clase que encapsula toda la comunicación: recursos utilizados, estado de
        la comunicación, etc.
    """
    
    def __init__(self, addr, logger, storage):
        # Recursos para la comunicación
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.datagram_queue = Queue()
        self.addr = addr
        self.storage = storage        
        self.name = SELECTIVE_REPEAT
        
        # Contadores globales para el envío ordenado y checkeo de errores
        self.seq_num = 0 # Número de secuencia del último paquete enviado
        self.ack_num = 0 # Número de secuencia del último paquete que se recibió correctamente y en orden.
        # Recursos especificos de Selective Repeat
        self.window_size = 4
        self.paquetes_en_vuelo = 0
        self.awaited_ack = 0
        self.lastest_received_ack = 0
        # self.already_acked_pkgs = {}

        self.arriving_pkt_buffer = {}
                         
        self.logger = logger

        self.timer = None # Timer que se usa para el handshake y para el FIN
        self.timers = {} # Map(seq_number, thread.Timer)
        self.last_sent_pkg = None  # Almacena el último paquete enviado. TODO: debería ser un map esto también
        
    # TODO: hay cosas que siguen rompiendo en stop and wait. Traer los cambios acá cuando funcione    
########################################################################################################################################
#########################--------HANDSHAKE--------##############################################################################################
      
    def start_server(self):
        """ Empieza a consumir paquetes"""        
        notTransfering=True
        while notTransfering:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
            pkg = Package.decode_pkg(datagram)
        
            if pkg.flags == SYN: 
                self.logger.info(f"[{self.addr}] Received SYN")
                #self.ack_num = pkg.seq_number + 1
                self.send_acknowledge('SYNACK', None)
            
            if pkg.flags == START_TRANSFER:
                self.logger.info(f"[{self.addr}] Received START_TRANSFER")
                self.send_acknowledge('ACK', pkg.seq_number)

                # TODO: hay que lanzar un thread acá para seguir escuchando los paquetes que llegan
                if pkg.type == UPLOAD_TYPE:
                    self.logger.info(f"[{self.addr}] Client is UPLOADING file")
                    self.receive_file(self.storage, pkg.data.decode())
                    notTransfering = False
                    
                if pkg.type == DOWNLOAD_TYPE:
                    self.logger.info(f"[{self.addr}] Client is DOWNLOADING file")
                    self.send_file(self.storage + "/" + pkg.data.decode())
                    notTransfering = False
                    
            if pkg.flags == ACK: # muerte ACÁ SOLO ENTRA EL SENDER (ENVIANDO UN FILE)
                self.logger.debug(f"[{self.addr}] Recibí un ACK del paquete {pkg.ack_number}")
                self.timers[pkg.seq_number].cancel()
    
    def start_client(self, client_type, args):
        self.logger.debug("Selective Repeat")
        # Primer mensaje solo tiene el SYN en 1 y si es de tipo download o upload
        # El server contesta con un SYN 1 y el ACK
        # El cliente envía un ACK con SYN 0 y la conexión queda establecida
        self.logger.info(f"[{self.addr}] Sending SYN")
        self.send_package(client_type, SYN, len(self.name.encode()), self.name.encode(), self.seq_num, self.ack_num)
        
        # Cuando hago un send_file, tengo que lanzar otro thread, con el recv_file no hace falta
        startedTransfer = False
        file_name = args.name
        
        while not startedTransfer:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
            pkg = Package.decode_pkg(datagram)
        
            if pkg.flags == SYNACK:
                self.logger.info(f"[{self.addr}] Recibí SYNACK, envio START_TRANSFER")
                self.send_package(client_type, START_TRANSFER, len(file_name), file_name.encode(), self.seq_num, self.ack_num)
                self.ack_num+=1
                self.awaited_ack += 1
                self.awaited_ack += 1

            if pkg.flags == ACK and not startedTransfer:
                self.logger.info(f"[{self.addr}] Recibí ACK del START_TRANSFER")
                self.ack_num+=1
                self.awaited_ack += 1
                self.awaited_ack += 1
                self.timer.cancel() # Sino sigue reenviando START_TRANSFER para siempre

                if client_type == DOWNLOAD_TYPE:
                    startedTransfer = True
                    self.receive_file(args.dst, file_name)
                    
                if client_type == UPLOAD_TYPE:
                    startedTransfer = True
                    self.send_file(args.src)
            
            # elif pkg.flags == ACK: # muerte ACÁ SOLO ENTRA EL SENDER (ENVIANDO UN FILE)
            #     self.logger.debug(f"[{self.addr}] Recibí un ACK para el paquete {pkg.ack_number}")
            #     if pkg.ack_number in self.timers:
            #         self.timers[pkg.ack_number].cancel()
            #         self.paquetes_en_vuelo -= 1
            #     else:
            #         self.logger.debug(f"[{self.addr}] Recibí un FINACK")
            #         if self.timer is not None:
            #             self.timer.cancel()

    def push(self, datagram: bytes):    
        self.datagram_queue.put(datagram)
    
########################################################################################################################################
#########################--------SENDER--------##############################################################################################
    def send_file(self, file_path):
        file, file_size = prepare_file_for_transmission(file_path)
        while file_size > 0:
            self.logger.info(f"\n[{self.addr}] File size remaining: {file_size}")
            
            while ((self.paquetes_en_vuelo < self.window_size)):             
                data = file.read(DATA_SIZE)
                data_length = len(data)               
                # El orden de los self.logger.debugs altera el producto
                self.logger.info(f"[{self.addr}] Sending {data_length} bytes in package {self.seq_num}")
                self.send_package(2, NO_FLAG, data_length, data, self.seq_num, self.seq_num)      
              
                self.paquetes_en_vuelo += 1 # Agregar paquetes en vuelo es solo una vez que se es sender (NO agregar a send_package() )
                self.logger.info(f"[{self.addr}] Paquetes en vuelo: {self.paquetes_en_vuelo}\n")
                
                file_size -= data_length
                
                #if ack_pkg.ack_number == self.seq_num:
                #    self.logger.info(f"Duplicated ACK {ack_pkg.ack_number} while self.seq_num {self.seq_num} from {self.addr}")
                #    raise Exception
                
                #self.seq_num+=1
            
           
            self.get_acknowledge()
            
            if (self.awaited_ack < self.lastest_received_ack):
                self.handle_unordered_package_by_sender(self.lastest_received_ack)
                
                #Voy checkeando en orden que paqutes ya fueron ackeados
                for seq_number in self.already_acked_pkgs:
                    #Si cumplen con el orden sigo
                    # while (pkg_in_buffer) in self.arriving_pkt_buffer:
                    #         pkg = self.arriving_pkt_buffer.pop(pkg_in_buffer)
                    #         file.write(pkg.data)
                    #         pkg_in_buffer += 1
                    pkg = self.already_acked_pkgs.pop(seq_number)
                    
                    if pkg.seq_number == self.awaited_ack:
                        self.awaited_ack += 1
                        self.lastest_received_ack = pkg.seq_number
                        pkg += 1
                    #Si no cumplen con el orden, significa que sigo teniendo algo perdido
                    else:
                        self.handle_unordered_package_by_sender(pkg)
        
        ##Si todavia no tengo lugar en paquetes_en_vuelo para el FIN, deberia esperar a un ACK...
        self.logger.debug("Salgo del loop principal")
        
        enviado_fin = False
        while(self.paquetes_en_vuelo > 0):
            self.logger.debug("La cantidad de paquetes en vuelo es: ", self.paquetes_en_vuelo)
            if (self.paquetes_en_vuelo == (self.window_size - 1) and not enviado_fin):
                self.send_package(2, FIN, 0, ''.encode(), self.seq_num, self.ack_num)     
                enviado_fin = True 
                self.paquetes_en_vuelo += 1
                self.logger.info(f"[{self.addr}] Sending FIN")                
                if self.timer is not None:
                    self.timer.cancel() # Apago timer
        
            self.get_acknowledge()
            
            if (self.awaited_ack < self.lastest_received_ack):
                self.handle_unordered_package_by_sender(self.lastest_received_ack)
                
                #Voy checkeando en orden que paqutes ya fueron ackeados
                for seq_number in self.already_acked_pkgs:
    
                    pkg = self.already_acked_pkgs.pop(seq_number)
                    
                    if pkg.seq_number == self.awaited_ack:
                        self.awaited_ack += 1
                        self.lastest_received_ack = pkg.seq_number
                        pkg += 1
                    #Si no cumplen con el orden, significa que sigo teniendo algo perdido
                    else:
                        self.handle_unordered_package_by_sender(pkg)
   
        self.logger.debug("Terminé send_file")
      
    def get_acknowledge(self):
        datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
        pkg = Package.decode_pkg(datagram)
        
        if pkg.flags == ACK:
            self.logger.debug(f"[{self.addr}] Recibí un ACK para el paquete {pkg.seq_number}")
            self.lastest_received_ack = pkg.seq_number
            # self.already_acked_pkgs[pkg.seq_number] = pkg

            if pkg.ack_number == self.awaited_ack: # Recibí en el orden correcto
                self.awaited_ack += 1

            if pkg.ack_number in self.timers:
                self.timers[pkg.ack_number].cancel()
                self.paquetes_en_vuelo -= 1
            else:
                self.logger.debug(f"[{self.addr}] Recibí un FINACK")
                self.paquetes_en_vuelo -= 1
                if self.timer is not None:
                    self.timer.cancel()
            return pkg
        
        last_pkg = Package.decode_pkg(self.last_sent_pkg)
        
        if pkg.flags == SYN:
            if pkg.ack_number == last_pkg.seq_number: #caso de ack no duplicado
                #("reinicio timer")
                if self.timer is not None:
                    self.timer.cancel()
                    # self.logger.debug("apago timer")
                #self.start_timer()  #Reinicio el timer porque recibio un ACK
                self.ack_num+=1
            return pkg
    
        if pkg.flags == SYNACK:
            if pkg.ack_number == last_pkg.seq_number: #caso de ack no duplicado
                #("reinicio timer")
                if self.timer is not None:
                    self.timer.cancel()
                    # self.logger.debug("apago timer")
                #self.start_timer()  #Reinicio el timer porque recibio un ACK
                self.ack_num+=1
            return pkg
        
        if pkg.flags == START_TRANSFER:
            self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
            return pkg
   
    def handle_unordered_package_by_sender(self, seq_number):
        """ Puramente para debugging """
        # TODO: en selective repeat devolver ACKs independientemente del desorden
        # y guardar data en buffer
        self.logger.info(f"[{self.addr}] Unordered package received:")
        self.logger.info(f"    Expected seq_number {self.awaited_ack}")
        self.logger.info(f"    Got seq_number {self.lastest_received_ack}")       

        self.get_acknowledge()
        if (self.awaited_ack != self.lastest_received_ack):
                self.handle_unordered_package_by_sender(self.lastest_received_ack)
                
        else:            
            self.logger.info(f"Got awaited ACK {self.awaited_ack}")
            self.awaited_ack += 1
            
        return
   
########################################################################################################################################
#########################--------RECEIVER--------##############################################################################################

    def receive_file(self, destination_path, file_name):
        self.logger.info(f"[{self.addr}] Beginning to receive file")
        # Estás recibiendo un archivo => solo mandas ACKs => ya no sos el sender
        # => no te encargas del timeout
        if self.timer is not None:
            self.timer.cancel()
    
        file = open(destination_path + "/" + file_name, "wb+")

        keep_receiving = True
        while keep_receiving:
            datagram = self.datagram_queue.get(block=True, timeout=CONNECTION_TIMEOUT)
            pkg = Package.decode_pkg(datagram)
            
            if pkg.flags == START_TRANSFER: # TODO: checkear como manejarlo dentro de start_server
                self.logger.debug("START TRANSFER DUPLICATED")
                self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
                
            elif pkg.flags == NO_FLAG: # Recibí bytes del archivo
                self.logger.info(f"[{self.addr}] Received package {pkg.seq_number}")
                # self.logger.debug(f"[{self.addr}] SEQ_NUMBER", pkg.seq_number)
                # self.logger.debug(f"[{self.addr}] ACK_NUMBER",self.ack_num)
                
                # TODO: está recibiendo seq = 2 y tiene ack en 0
                
                # Caso ideal: me llego el paquete en el orden correcto
                if pkg.seq_number == self.ack_num:
                    file.write(pkg.data)
                    #Si el paquete que me llegó era el perdido que esperaba
                    #me fijo lo que tenga en el buffer y lo escribo en el archivo
                    if(pkg.seq_number + 1) in self.arriving_pkt_buffer:
                        pkg_in_buffer = pkg.seq_number + 1
                        while (pkg_in_buffer) in self.arriving_pkt_buffer:
                            pkg = self.arriving_pkt_buffer.pop(pkg_in_buffer)
                            file.write(pkg.data)
                            pkg_in_buffer += 1
                            ##ESTAMOS ACTUALIZANDSO EL SEQ_NUMBER (el expected packet?)
                    #Una vez escrito el archivo de forma ordenada, mando el ACK pendiente
                    self.send_acknowledge('ACK', pkg.seq_number)
                    
                
                # Casos de falla
                elif pkg.seq_number == (self.ack_num - 1): # Paquete duplicado (caso que ack no llega)
                    self.send_acknowledge('DUPLICATE_ACK', pkg.seq_number)
                    continue

                #El receiver recibe un paquete fuera de orden. Lo guardo en el buffer.
                if self.ack_num > pkg.seq_number + 1: 
                    handle_unordered_package_by_receiver(pkg)
                   
                
                if pkg.seq_number == 0: #caso que recibe despues de una retransmicion
                    self.ack_num=0
            
            elif pkg.flags == FIN:
                # TODO: meter un handle_fin o end o algo
                self.logger.debug("recibo FIN y mando ACK", pkg.seq_number)
                self.send_acknowledge('ACK', pkg.seq_number)
                if self.timer is not None:
                    self.timer.cancel()
                    # self.logger.debug("apago timer")
                
                keep_receiving = False
            
                
        self.logger.info(f"[{self.addr}] File {file_name} received")
    
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
      
    def handle_unordered_package_by_receiver(self, pkg):
        # self.logger.info(f"Wrong self.ack_num = {self.ack_num} and  pkg.seq_number + 1 = {pkg.seq_number + 1}")
        self.arriving_pkt_buffer[pkg.seq_number] = pkg
        #A diferenca de SW, mando ACK igual, aunque este en desorden
        #Que no me cambie el ack actual! Yo sigo esperando el paquete perdido.
        self.send_acknowledge('ACK', pkg.seq_number)   

########################################################################################################################################

    def start_timer(self, pkg: Package):
        """ Esta función la usas en el handshake y el FIN"""
        if self.timer is not None:
            self.timer.cancel()  # Cancela el timer anterior si existe

        self.timer = threading.Timer(PKG_TIMEOUT, self.handle_timeout, args=(pkg,))
        self.timer.start()
    
    def start_concurrent_timer(self, pkg: Package):
        """ Esta función la usas para cuando queres tener múltiples timers"""
        # TODO: hacer que se manejen multiples timers
        if pkg.seq_number in self.timers and self.timers[pkg.seq_number] is not None:
            self.timers[pkg.seq_number].cancel()  # Cancela el timer anterior si existe

        self.timers[pkg.seq_number] = threading.Timer(PKG_TIMEOUT, self.handle_timeout, args=(pkg,))
        self.logger.debug(f"Arranco un timer para el paquete {pkg.seq_number}")
        self.timers[pkg.seq_number].start()

    def handle_timeout(self, pkg: Package):
        """ Se llama cuando se agota el temporizador (timeout) """
        if self.last_sent_pkg is not None:
            
            self.logger.info(
                f"[{self.addr}] RETRANSMITO " +
                f"paquete: {pkg.seq_number} | flag: {pkg.flags}"
            )
            
            self.socket.sendto(pkg.encode_pkg(), self.addr)

            self.start_concurrent_timer(pkg) # Reinicia el temporizador para este paquete
            # self.logger.debug("prendo timer")
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
        )     
    
        # self.logger.debug(type, flag, seq_number, ack_number)
        self.socket.sendto(pkg.encode_pkg(), self.addr)
        
        self.seq_num += 1
        
        # Guarda el último paquete enviado para retransmitirlo en caso de timeout
        self.last_sent_pkg = pkg
        if flag == NO_FLAG: # Paquetes con data
            self.start_concurrent_timer(pkg)
        elif flag == SYN or flag == START_TRANSFER or flag == FIN: # Paquetes del sender en el handshake
            self.start_timer(pkg)
        else:
            self.ack_num += 1