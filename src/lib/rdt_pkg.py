# Por ahora este es el archivo que tiene todo lo relacionado con el armado y 
# extracción de paquetes

""" Clase que se encarga de crear y extraer paquetes RDT """
class RDTPackage:
    # Init deja al paquete listo para ser enviado
    def __init__(self, seq_num: int, data: bytes):
        # Header
        self.seq_num = seq_num
        
        self.data = data
        self.pkg = self._encode()
        
    # Para debuggear
    def __str__(self):
        return f"""RDTPackage(          
            seq_num={self.seq_num},   
            data={self.data}          
        )"""
        
    def _encode(self):
        pkg = bytes()
        pkg += self.seq_num.to_bytes(4, 'big')
        pkg += self.data
        return pkg
    
    @staticmethod
    def extract(pkg: bytes):
        # TODO: manejo de errores
        seq_num = int.from_bytes(pkg[:4], 'big')
        data = pkg[4:]
        
        return RDTPackage(seq_num, data)
