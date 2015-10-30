import binascii
import socket
import sys
from struct import *

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 2463)
sock.connect(server_address)


packed_data = b'\x80\x00\x00\x28'

sock.sendall(packed_data)

#Просто плюем в сервер 40 байт
packed_data = b'\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28\x80\x00\x00\x28'
#Он выплевывает что-то иногда, а иногда выплевывает 4 байта
sock.sendall(packed_data)

tmp = sock.recv(40000)
print(binascii.hexlify(tmp))
print("\n")