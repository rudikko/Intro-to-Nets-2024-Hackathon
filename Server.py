import socket
import threading
import time
import struct
import random

# Constants given in the assignment
MAGIC_COOKIE = 0xabcddcba
# msg types that are from server to client
MSG_TYPE_OFFER = 0x2
MSG_TYPE_PAYLOAD = 0x4
CONST_SIZE = 1024
UDP_BROADCAST_PORT = 39457 # Client Port number for broadcasting UDP packets

def find_available_port(start_port, end_port, protocol):
    """
    Find an available port within a given range.
    Returns An available port number that the server will listen on.
    """
    if protocol == 'tcp':
        sock_type = socket.SOCK_STREAM # create tcp socket
    elif protocol == 'udp':
        sock_type = socket.SOCK_DGRAM # create udp socket

    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, sock_type) as sock: # when the socket is closed, the port is released
            try:
                # Try binding to the port
                sock.bind(('0.0.0.0', port))
                return port  # Return the available port number
            except OSError:
                continue  # If port is occupied, try the next one


def broadcast_offers(server_ip,udp_port,tcp_port):
    """
    Broadcasts offers to all clients on the network.
    """
    while True:
            
        # Create the offer packet , the packet is a 10 byte packet with the following structure , magic cookie is 4 bytes, message type is 1 byte, udp port is 2 bytes and tcp port is 2 bytes.
        offer_packet = struct.pack('!IBHH', MAGIC_COOKIE, MSG_TYPE_OFFER, udp_port, tcp_port)
            
        # Set up the socket to broadcast the offer message
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # IPv4, UDP socket
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # allowing broadcast for the socket
        broadcast_socket.sendto(offer_packet, ('<broadcast>', UDP_BROADCAST_PORT)) # broadcast the offer packet to all clients on the network.
            
        time.sleep(1) # broadcast offers every second


def start_server():
    server_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server started, listening on IP address {server_ip}")
    udp_port = find_available_port(1025, 65535, 'udp') # find an available port for UDP , skip 1024 OS ports.
    tcp_port = find_available_port(1025, 65535, 'tcp') # find an available port for TCP , skip 1024 OS ports.
    threading.Thread(target=broadcast_offers, args=(server_ip,udp_port,tcp_port), daemon=True).start() # start a new thread that will be responsible for broadcasting offers

    # Set up the socket to listen for incoming connections - tcp
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((server_ip, tcp_port))
    tcp_socket.listen(7) # maximum number of queued connection requests that can wait to be accepted
    tcp_socket.setblocking(False) # make the socket non-blocking - the accept() method will not block the program

    # Set up the socket to listen for incoming connections - udp
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_ip, udp_port))
    udp_socket.setblocking(False) # make the socket non-blocking - the recvfrom() method will not block the program


    while True:
        try:
            # try to accept incoming tcp connections
            conn, addr = tcp_socket.accept()
            threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()
        except BlockingIOError: # in case there are no incoming connections
            pass
        
        try:
            # try to receive incoming udp packets
            data, addr = udp_socket.recvfrom(CONST_SIZE)
            threading.Thread(target=handle_udp_client, args=(data, addr), daemon=True).start()
        except BlockingIOError: # in case there are no incoming packets
            pass

        
    



if __name__ == "__main__":
    start_server()