from lib.values import *

class StopAndWaitProtocol():
    def __init__(self):
        self.seq_num = 0
        self.ack_num = 1
        self.tries_send = 0
        self.name = STOP_AND_WAIT