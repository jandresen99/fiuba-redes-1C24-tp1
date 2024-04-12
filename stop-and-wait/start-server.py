import socket
import argparse

def start():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 6000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print("Listening on {}:{}".format(UDP_IP, UDP_PORT))

    while True:
        data, addr = sock.recvfrom(1024)
        print("Message received:", data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='start-server')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    parser.add_argument('-H', '--host', default='localhost', help='service IP address')
    parser.add_argument('-p', '--port', type=int, default=8080, help='service port')
    parser.add_argument('-s', '--storage', required=True, help='storage dir path')

    args = parser.parse_args()

    if args.verbose:
        print("verbosity activated")
    elif args.quiet:
        print("quiet activated")
