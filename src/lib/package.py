from lib.values import *

def add_padding(data: bytes, n: int):
    k = n - len(data)
    if k < 0:
        raise ValueError
    return data + b"\0" * k

class Package:
    def __init__(self, type, flags, data_length, data: bytes, seq_number=0, ack_number=0):
        self.type = type
        self.flags = flags # 8 bits, se lee como un nº asociado a un único flag
        self.data_length = data_length
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.data = data
        
    # Para infogear
    def __str__(self):
        return f"""Package(
            Type: {self.type},
            Flags: {self.flags},
            Data Length: {self.data_length},
            Seq Number: {self.seq_number},
            Ack Number: {self.ack_number},
            Data: {self.data}          
        )"""
    
    def encode_pkg(self) -> bytes:
        bytes_arr = b""
        bytes_arr += self.type.to_bytes(1, byteorder='big')
        bytes_arr += self.flags.to_bytes(1, byteorder='big')
        bytes_arr += self.data_length.to_bytes(4, signed=False, byteorder='big')
        bytes_arr += self.seq_number.to_bytes(4, byteorder='big', signed=False)
        bytes_arr += self.ack_number.to_bytes(4, byteorder='big', signed=False)

        bytes_arr += add_padding(self.data, BUFFER_SIZE - len(bytes_arr))

        return bytes_arr
    
    @classmethod
    def decode_pkg(cls, bytes_arr):
        flags = bytes_arr[1]
        data_length = int.from_bytes(bytes_arr[2:6], byteorder="big")
        seq_number = int.from_bytes(bytes_arr[6:10], byteorder="big")
        ack_number = int.from_bytes(bytes_arr[10:14], byteorder="big")
        data = bytes_arr[14: 14 + data_length]

        if bytes_arr[0] == 1 or bytes_arr[0] == 2:
            type = bytes_arr[0]
        else:
            raise ValueError
        
        return Package(type, flags, data_length, data, seq_number, ack_number)
    