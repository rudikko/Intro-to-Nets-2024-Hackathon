import socket
import threading
import time
import struct
import random
from configs import *
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)


def find_available_port(start_port, end_port, protocol):
    """
    Find an available port within a given range.
    Returns an available port number that the server will listen on.
    """
    if protocol == 'tcp':
        sock_type = socket.SOCK_STREAM  # create tcp socket
    elif protocol == 'udp':
        sock_type = socket.SOCK_DGRAM  # create udp socket

    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, sock_type) as sock:  # when the socket is closed, the port is released
            try:
                # Try binding to the port
                sock.bind(('0.0.0.0', port))
                return port  # Return the available port number
            except OSError:
                continue  # If port is occupied, try the next one

    raise RuntimeError("No available port found in the specified range.")


def broadcast_offers(udp_port, tcp_port):
    """
    Broadcasts offers to all clients on the network.
    """
    try:
        while True:
            # Create the offer packet , the packet is a 10 byte packet with the following structure , magic cookie is 4 bytes, message type is 1 byte, udp port is 2 bytes and tcp port is 2 bytes.
            offer_packet = struct.pack('!IBHH', MAGIC_COOKIE, MSG_TYPE_OFFER, udp_port, tcp_port)

            # Set up the socket to broadcast the offer message
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # IPv4, UDP socket
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # allowing broadcast for the socket
            broadcast_socket.sendto(offer_packet, (BROADCOAST_IP, UDP_BROADCAST_PORT))  # broadcast the offer packet to all clients on the network.

            time.sleep(1)  # broadcast offers every second
    except Exception:
        print(Fore.RED + "Error occurred while broadcasting offers.")


def handle_tcp_client(clientconn, addr):
    """
    Handles incoming TCP connections, addr is a tuple made up of the client's IP address and port number.
    """
    print(Fore.GREEN + f"TCP Client connected from {addr}")
    try:

        file_size_bytes = clientconn.recv(CONST_SIZE).decode().strip()  # read CONST_SIZE bytes of data and convert it to a string without leading or trailing whitespaces
        file_size = int(file_size_bytes)  # convert the string to an integer

        already_sent = 0  # number of bytes sent to the client
        single_transmission = CONST_SIZE * 8  # number of bytes to send in a single transmission - 8KB

        while already_sent < file_size:
            # send the file in chunks of 8KB
            left_to_send = file_size - already_sent  # number of bytes left to send
            to_send = min(single_transmission, left_to_send)
            data = bytearray(random.getrandbits(8) for _ in range(to_send))  # generate random bytes to send to the client
            try:
                clientconn.sendall(data)  # send the data to the client
            except Exception:
                break  # Break the loop if the client disconnects unexpectedly
            already_sent += to_send
        
    except:
        pass
    finally:
            print(Fore.BLUE + f"TCP Client disconnected from {addr}")
            clientconn.close()  # close the connection


def handle_udp_client(data, addr):
    """
    Handles incoming UDP packets, 'addr' is a tuple made up of the client's IP address and port number.
    """
    magic_cookie, msg_type, file_size = struct.unpack('!IBQ', data)  # Unpack the received packet to get the magic cookie, message type, and file size

    # Validate the magic_cookie and message type
    if magic_cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST:
        print(Fore.RED + "Invalid magic cookie or message type.")
        return
    
    total_segments = (file_size + CONST_SIZE - 1) // CONST_SIZE  # Calculate the total number of segments to send

    # Create a new UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
        
        # Send segments dynamically in a loop
        burst_size = 64  # Number of segments to send in a single burst
        for segment_num in range(total_segments):
            remaining = file_size - (segment_num * CONST_SIZE)
            current_segment_size = min(CONST_SIZE, remaining)
                
            # Generate the payload with random data (the "actual" data)
            payload = bytearray(random.getrandbits(8) for _ in range(current_segment_size))
                
            # Prepare the header of the payload message
            header = struct.pack('!IBQQ', 
                MAGIC_COOKIE,
                MSG_TYPE_PAYLOAD,
                total_segments,
                segment_num
            )
            
            # Send the segment
            send_socket.sendto(header + payload, addr)

            # Send in bursts to reduce congestion
            if (segment_num + 1) % burst_size == 0:
                time.sleep(0.001)  # Small delay to prevent congestion
        

def start_server():
    """
    Starts the server, creates the broadcast thread and listens for incoming connections.
    """
    server_ip = socket.gethostbyname(socket.gethostname())
    print(Fore.YELLOW + f"Team {TEAM_NAME} Server started, listening on IP address {server_ip}")
    udp_port = find_available_port(1025, 65535, 'udp')  # find an available port for UDP , skip 1024 OS ports.
    tcp_port = find_available_port(1025, 65535, 'tcp')  # find an available port for TCP , skip 1024 OS ports.
    threading.Thread(target=broadcast_offers, args=(udp_port, tcp_port), daemon=True).start()  # start a new thread that will be responsible for broadcasting offers

    # Set up the socket to listen for incoming connections - tcp
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen(7)  # maximum number of queued connection requests that can wait to be accepted
    tcp_socket.setblocking(False)  # make the socket non-blocking - the accept() method will not block the program

    # Set up the socket to listen for incoming connections - udp
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', udp_port))
    udp_socket.setblocking(False)  # make the socket non-blocking - the recvfrom() method will not block the program

    while True:
        try:
            # try to accept incoming tcp connections
            conn, addr = tcp_socket.accept()
            threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()
        except BlockingIOError:  # in case there are no incoming connections
            pass
        
        try:
            # try to receive incoming udp packets
            data, addr = udp_socket.recvfrom(CONST_SIZE)
            threading.Thread(target=handle_udp_client, args=(data, addr), daemon=True).start()
        except BlockingIOError:  # in case there are no incoming packets
            pass


if __name__ == "__main__":
    start_server()
