import socket
import struct
import threading
import time
from configs import *
from colorama import Fore, Style, init

# Initialize colorama for cross-platform compatibility
init(autoreset=True)


def startup():
    """
    Asking the user for the file size and number of connections.
    """
    while True:
        try:
            file_size = int(input("Enter file size (bytes): "))
            tcp_num = int(input("Enter number of TCP connections: "))
            udp_num = int(input("Enter number of UDP connections: "))
            if file_size <= 0 or tcp_num <= 0 or udp_num <= 0:
                raise ValueError()
            return file_size, tcp_num, udp_num
        except ValueError as e:
            print(Fore.RED + "Invalid input. Please enter positive numbers only.")

def waitforoffers():
    """
    Function to wait for offers from the server, it will keep listening for offers until it receives a valid offer.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', UDP_BROADCAST_PORT))

    while True:
        try:
            data, addr = udp_socket.recvfrom(CONST_SIZE) # receive data from the server
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data) # unpack the received data

            if magic_cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER: # validate the magic cookie and message type
                print(Fore.GREEN + f"Received offer from {addr[0]}")
                return addr[0], udp_port, tcp_port
            else:
                print(Fore.RED + "Invalid magic cookie or message type.")
        except Exception:
            print(Fore.RED + "Error occurred while waiting for offers.")

def handle_tcp(server_ip, tcp_port, file_size, conn_num):
    """
    Function to handle TCP connections, it will connect to the server and receive the data.
    """
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, tcp_port))

        tcp_socket.send(f"{file_size}\n".encode()) # sent amount of data required for transfer in bytes as a regular string followed by a \n

        start_time = time.time()

        already_received = 0
        single_transmission = CONST_SIZE * 8
        while already_received < file_size:
            to_recieve = tcp_socket.recv(min(single_transmission, file_size - already_received)) 
            if not to_recieve:
                break  # Stop if no more data is received (connection closed)
            already_received += len(to_recieve)
        
        end_time = time.time()

        total_time = end_time - start_time
        transmission_speed = file_size / total_time # that is in bytes per second, to convert to bits per second, multiply by 8
        transmission_speed_bits = transmission_speed * 8

        # print desired output as in the assignment
        print(Fore.GREEN + f"TCP transfer #{conn_num} finished, "
                          f"total time: {total_time:.2f} seconds, "
                          f"total speed: {transmission_speed_bits:.1f} bits/second")
            
    except Exception as e:
        print(Fore.RED + "Error occurred while handling TCP connection.")
    finally:
        tcp_socket.close()

def handle_udp(server_ip, udp_port, file_size, conn_num):
    """
    Function to handle UDP connections, it will connect to the server and receive the data.
    """
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(1)  # Set timeout , if we don't recieve anything for a seconed consider the transfer complete
        udp_socket.sendto(struct.pack('!IBQ', MAGIC_COOKIE, MSG_TYPE_REQUEST, file_size), (server_ip, udp_port)) # build and send the request to the server

        start_time = time.time()
        total_segments = (file_size + 1024 - 1) // 1024 # calculate the total number of segments to send, an additional segment is needed if the file size is not a multiple of 1024
        received_segments = {}  # Dictionary to track received segments by sequence number
        received_bytes = 0  # Track the total number of bytes received

        while True:
            try:
                data, _ = udp_socket.recvfrom(CONST_SIZE * 32)  # Receive a segment 16KB

                # Unpack the header: MAGIC_COOKIE, MSG_TYPE, total segments, and current segment number
                header_size = struct.calcsize('!IBQQ') # we calculate it in order to find the data size later
                magic_cookie, msg_type, total_segments, current_seg = struct.unpack('!IBQQ', data[:header_size])

                # Validate magic cookie and message type to ensure we are receiving valid data
                if magic_cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
                    print(Fore.RED + "Invalid magic cookie or message type.")
                    continue

                # Calculate the actual data size in the packet (after the header)
                data_size = len(data) - header_size
                if current_seg not in received_segments:
                    received_segments[current_seg] = data_size
                    received_bytes += data_size

            except socket.timeout:
                    break

        # Calculate total transfer time and speed
        total_time = time.time() - start_time
        success_rate = (len(received_segments) / total_segments) * 100
        transmission_speed_bits = (received_bytes * 8) / total_time  # Speed in bits per second

        print(Fore.GREEN + f"UDP transfer #{conn_num} finished, "
                          f"total time: {total_time:.2f} seconds, "
                          f"total speed: {transmission_speed_bits:.1f} bits/second, "
                          f"percentage of packets received successfully: {success_rate:.0f}%")

    except Exception as e:
        print(Fore.RED + f"Error occurred during UDP transfer #{conn_num}: {str(e)}")
    finally:
        udp_socket.close()

def startclient():
    """
    Main function to start the client, it will keep listening for offers and start the transfers when it receives an offer,
    each connection has its own thread.
    """
    file_size, tcp_num, udp_num = startup()
    while True:
        print(Fore.YELLOW + f"Team {TEAM_NAME} Client started, listening for offer requests...")
            
        server_ip, udp_port, tcp_port = waitforoffers()
            
        threads = [] # create a list to store the threads we will create for each connection
        # Create TCP thread for each tcp connection.
        threads.extend(
            threading.Thread(target=handle_tcp, args=(server_ip, tcp_port, file_size, i + 1)) # start from i+1 for transmission number
            for i in range(tcp_num)
        )

        # Create UDP threads for each udp request.
        threads.extend(
            threading.Thread(target=handle_udp, args=(server_ip, udp_port, file_size, i + 1)) # start from i+1 for transmission number
            for i in range(udp_num)
        )

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        
        # After it is done, keep listening for offers
        print(Fore.YELLOW + "All transfers complete, listening to offer requests")
    
if __name__ == "__main__":
    startclient()
