''' Santricity diagnostic info collector '''

import socket
import struct
import sys
import time
import binascii

class SantriClient:
    ''' Santricity client that sends the packets to the server
        and transmits the response from the server to parser
    '''

    def __init__(self, host, port):
        self.time_sign = self.generate_session_signature()
        self.host = host
        self.port = port


    def generate_session_signature(self):
        ''' Generates a time signature for the current session '''
        #TODO: написать код для генерирования сигнатуры
        return b'\55\6c\31\77'

    def generate_packet(self, packet_code):
        ''' Generates the package on the signature of the session
            and the request code
        '''
        if (packet_code == '040'):
            packet_data = self.time_sign + b'\00\00\00\00' + b'\00\00\00\02' + b'\53\69\4d\42' + b'\00\00\00\01' + b'\00\00\00\28' + 4*b'\00\00\00\00'
        return packet_data

    def show(self, command):
        ''' Returns the response to a request in a readable form '''
        if (command == 'bigdata'):
            request = self.generate_packet('040')
            self.get_data(request)

    def get_data(self, request):
        ''' Returns the data which have been received from the server '''
        conn = socket.socket()
        conn.connect( (self.host, self.port) )

        length_packet = self.generate_length_packet(len(request))
        conn.send(length_packet)
        print ('Send packet' + binascii.hexlify(length_packet))
        conn.send(request)
        data = b""
        tmp = self.conn.recv(1024)
        while tmp:
            data += tmp
            tmp = conn.recv(1024)
        print( binascii.hexlify(data) )
        conn.close()

    def generate_length_packet(self, length):
        length_pack = bytearray(b'\x80\x00\x00')
        length_pack.extend(b'\28')
        return length_pack

class SantriParser:
    ''' Santricity parser of raw data '''

    def parse_data(self, data, command):
        ''' Receives the data as an array of bytes from the server
            and returns the required data in a readable format
        '''

if __name__ == '__main__':
    my_sm_cli = SantriClient('localhost', 2463)
    my_sm_cli.show('bigdata')
