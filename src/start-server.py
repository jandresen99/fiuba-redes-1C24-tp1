import socket
import argparse
import logging

logger = logging.getLogger(__name__)

def start():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 6000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    logger.info("Listening on %s:%d", UDP_IP, UDP_PORT)

    while True:
        data, addr = sock.recvfrom(1024)
        logger.info("Message received: %s", data)

def menu():
    parser = argparse.ArgumentParser(prog='start-server')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    parser.add_argument('-H', '--host', help='service IP address', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, help='service port', metavar='PORT')
    parser.add_argument('-s', '--storage', help='storage dir path', metavar='DIRPATH')

    args = parser.parse_args()

    return args

def main():
    args = menu()

    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    logging.basicConfig(filename='server.log', level=level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    logger.addHandler(ch)

    start()



if __name__ == "__main__":
    main()


    
    
