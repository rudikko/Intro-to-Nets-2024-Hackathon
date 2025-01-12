import socket
import struct
import threading
import time
from configs import *


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
            print("Invalid input. Please enter positive numbers only.")

def waitforoffers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', UDP_BROADCAST_PORT))

    while True:
        try:
            data, addr = udp_socket.recvfrom(CONST_SIZE) # receive data from the server
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data) # unpack the received data

            if magic_cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER:
                print(f"Received offer from {addr[0]}")
                return addr[0], udp_port, tcp_port
        except Exception:
            print("Error occurred while waiting for offers.")

def startclient():
    file_size, tcp_num, udp_num = startup()

    
if __name__ == "__main__":
    startclient()