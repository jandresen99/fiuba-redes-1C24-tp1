# Por ahora este es el archivo que tiene todo lo relacionado con el armado y 
# extracción de paquetes

""" Clase que se encarga de crear y extraer paquetes RDT """
class RDTPackage:
    # Init deja al paquete listo para ser enviado
    def __init__(self, seq_num: int, data: bytes):
        # Header
        self.seq_num = seq_num
        self.checksum = self._checksum()
        
        self.data = data
        self.pkg = self._encode()
        
    # Para debuggear
    def __str__(self):
        return f"""RDTPackage(          
            seq_num={self.seq_num},   
            checksum={self.checksum}, 
            data={self.data}          
        )"""
        
    def _checksum(self):
        # Sumar de byte a byte y quedate con los primeros 16 bits, supongo que funca
        return bytearray(2)
        
    def _encode(self):
        pkg = bytes()
        pkg += self.seq_num.to_bytes(4, 'big')
        pkg += self.checksum
        pkg += self.data
        return pkg
        
    def get_pkg(self):
        return self.pkg
    
    @staticmethod
    def extract(pkg: bytes):
        # TODO: manejo de errores
        seq_num = int.from_bytes(pkg[:4], 'big')
        checksum = pkg[4:6] # TODO: validar el checksum
        data = pkg[6:]
        
        return RDTPackage(seq_num, data)
