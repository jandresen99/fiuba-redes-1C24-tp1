import logging
import os
from argparse import ArgumentParser
from lib.values import *

def set_logger(args, name):
    logger = logging.getLogger(name)
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
    return logger

def get_server_args():
    parser = ArgumentParser(prog='start-server')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    
    parser.add_argument('-H', '--host', default=SERVER_IP, help='server IP address. Defaults to 127.0.0.1', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='server port. Defaults to port 6000', metavar='PORT')
    parser.add_argument('-s', '--storage', default=STORAGE_LOCATION, help='storage dir path', metavar='DIRPATH')

    return parser.parse_args()

def get_upload_args():
    parser = ArgumentParser(description='Uploads a file to the server')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')

    parser.add_argument('-H', '--host', default=SERVER_IP, help='server IP address. Defaults to 127.0.0.1', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='server port. Defaults to port 6000', metavar='PORT')
    parser.add_argument('-s', '--src', help='source file path', metavar='FILEPATH', required=True)
    parser.add_argument('-n', '--name', help='file name', metavar='FILENAME', required=True)
    parser.add_argument('-t', '--protocol', choices=['sw', 'sr'], default='sw', help='protocol type. Defaults to Stop and Wait', metavar='PROTOCOL')
    return parser.parse_args()

def get_download_args():
    parser = ArgumentParser(description='Downloads a from the server')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')

    parser.add_argument('-H', '--host', default=SERVER_IP, help='server IP address. Defaults to 127.0.0.1', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='server port. Defaults to port 6000', metavar='PORT')
    parser.add_argument('-d', '--dst', default=DESTINATION_LOCATION, help='destination file path', metavar='FILEPATH')
    parser.add_argument('-n', '--name', help='file name', metavar='FILENAME', required=True)
    parser.add_argument('-t', '--protocol', choices=['sw', 'sr'], default='sw', help='protocol type. Defaults to Stop and Wait', metavar='PROTOCOL')

    return parser.parse_args()

def prepare_file_for_transmission(file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not existe")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"The file size of '{file_path}' is zero")
        
        file = open(file_path, "rb") # rb es para leer en binario

        return file, file_size