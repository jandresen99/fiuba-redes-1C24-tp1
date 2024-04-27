from lib.values import *

def add_padding(data: bytes, n: int):
    k = n - len(data)
    if k < 0:
        raise ValueError
    return data + b"\0" * k

class Package:
    def __init__(self, type, flags, data_length, file_name, data, seq_number=0, ack_number=0):
        self.type = type
        self.flags = flags
        self.data_length = data_length
        self.file_name = file_name
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.data = data
    
    def encode_pkg(self):
        bytes_arr = b""
        bytes_arr += self.type.to_bytes(1, byteorder='big')
        bytes_arr += self.flags.to_bytes(1, byteorder='big')
        bytes_arr += self.data_length.to_bytes(4,
                                               signed=False, byteorder='big')

        if self.file_name is not None:
            bytes_arr += add_padding(self.file_name.encode(), 400)

        bytes_arr += self.seq_number.to_bytes(4, byteorder='big', signed=False)
        bytes_arr += self.ack_number.to_bytes(4, byteorder='big', signed=False)

        # append data from position 1024 to 2048
        bytes_arr += add_padding(self.data, BUFFER_SIZE - len(bytes_arr))

        return bytes_arr
    
    @classmethod
    def decode_pkg(cls, bytes_arr):
        flags = bytes_arr[1]
        data_length = int.from_bytes(bytes_arr[2:6], byteorder="big")
        file_name = bytes_arr[6:406].decode().strip('\0')
        seq_number = int.from_bytes(bytes_arr[406:410], byteorder="big")
        ack_number = int.from_bytes(bytes_arr[410:414], byteorder="big")
        data = bytes_arr[414: 414 + data_length]

        if bytes_arr[0] == 1 or bytes_arr[0] == 2:
            type = bytes_arr[0]
        else:
            raise ValueError
        
        return Package(type, flags, data_length, file_name, data, seq_number, ack_number)
    
    @classmethod
    def handshake_pkg(cls, type, protocol):
        return Package(type, HELLO, len(protocol.name.encode()), "", protocol.name.encode()).encode_pkg()