import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 6000

MESSAGE = b"Hola!"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

print("Message sent:", MESSAGE)
