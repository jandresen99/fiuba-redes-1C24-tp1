from argparse import ArgumentParser

SERVER_IP = "127.0.0.1"
SERVER_PORT = 6000

def get_server_args():
    parser = ArgumentParser(prog='start-server')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')
    
    parser.add_argument('-H', '--host', default=SERVER_IP, help='server IP address. Defaults to 127.0.0.1', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='server port. Defaults to port 6000', metavar='PORT')
    parser.add_argument('-s', '--storage', help='storage dir path', metavar='DIRPATH')

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
    
    return parser.parse_args()

def get_download_args():
    parser = ArgumentParser(description='Downloads a from the server')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    group.add_argument('-q', '--quiet', action='store_true', help='decrease output verbosity')

    parser.add_argument('-H', '--host', default=SERVER_IP, help='server IP address. Defaults to 127.0.0.1', metavar='ADDR')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='server port. Defaults to port 6000', metavar='PORT')
    parser.add_argument('-d', '--src', help='destination file path', metavar='FILEPATH', required=True)
    parser.add_argument('-n', '--name', help='file name', metavar='FILENAME', required=True)
    
    return parser.parse_args()