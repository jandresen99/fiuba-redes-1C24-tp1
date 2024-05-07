from logging import Logger
from lib.values import *
from lib.stop_and_wait import StopAndWait
from lib.selective_repeat import SelectiveRepeat
from lib.utils import *
from threading import Thread
import random 
from lib.package import Package


# TODO: hacer que el cliente cierre solo cuando termina de enviar o recibir algo
# TODO: cuando el server no esta prendido, la aplicación cierra con error (super extra)
class Client:
    def __init__(self, ip, port, type, logger: Logger, destination, protocol: str):
        self.ip = ip
        self.port = port
        self.server_address = None
        self.logger = logger

        if protocol == STOP_AND_WAIT:
            self.protocol = StopAndWait((ip, port), logger, destination)
        elif protocol == SELECTIVE_REPEAT:
            self.protocol = SelectiveRepeat((ip, port), logger, destination)

        if type == UPLOAD_TYPE or type == DOWNLOAD_TYPE:
            self.type = type
        else:
            self.logger.error(f"Error: invalid type")
    
    def start(self, args):
        thread = Thread(target=self.protocol.start_client, args=(self.type, args))
        thread.start()
        
        while True:
            datagram, addr = self.protocol.socket.recvfrom(BUFFER_SIZE)

            rand_num = random.random() # Entre 0 y 1
            if rand_num < 0:
                num_package = Package.decode_pkg(datagram).seq_number
                print(f"\n[DROP] Se perdió el package {num_package} proveniente de {addr}")
                print(f"Flags: {Package.decode_pkg(datagram).flags}\n")
                continue

            self.protocol.push(datagram)
            