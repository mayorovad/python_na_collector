''' Santricity diagnostic info collector '''

import socket
import struct
import sys
import time
import binascii
import numpy

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

        session_sign = b'\x55\x6c\x31\x77'
        return session_sign

    def generate_packet(self, packet_code):
        ''' Generates the package on the signature of the session
            and the request code
        '''

        packet_data = bytearray()
        if (packet_code == '040'):
            packet_data.extend(self.time_sign)
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(self.int_to_4hex(2))
            packet_data.extend(b'\x53\x69\x4d\x42')
            packet_data.extend(self.int_to_4hex(1))
            packet_data.extend(self.int_to_4hex(40))
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(self.int_to_4hex(0))
        return packet_data

    def show(self, command):
        ''' Returns the response to a main_package in a readable form '''
        if (command == 'bigdata'):
            main_package = self.generate_packet('040')
            self.get_data(main_package)

    def get_data(self, main_package):
        ''' Returns the data which have been received from the server '''
        self.conn = socket.socket()
        self.conn.connect( (self.host, self.port) )

        #Делим на 2, так как нужна длина в байтах
        length_packet = self.generate_length_packet(len(main_package))
        main_packet = self.generate_packet(main_package)

        print ('Sending length_packet, main packet length is %i' % (len(main_package)))
        self.conn.send(length_packet)
        print ('Sending main package...')
        self.conn.send(main_package)

        print ('Receiving length_packet from server...')
        length_packet = self.conn.recv(4)
        need_to_recieve = int(binascii.hexlify(length_packet[-2::]), 16)
        remaining_bytes = need_to_recieve
        print(remaining_bytes)
        print('Receiving bigdata (%i bytes)' % (need_to_recieve))

        bigdata = b''
        tmp = self.conn.recv(4096)
        remaining_bytes -= 4096
        print('Remaining bigdata - %i bytes...)' % (remaining_bytes))
        while (remaining_bytes > 0):
            bigdata += tmp
            if (remaining_bytes < 4096):
                tmp = self.conn.recv(remaining_bytes)
                remaining_bytes -= remaining_bytes
            else:
                tmp = self.conn.recv(4096)
                remaining_bytes -= 4096
            print('Remaining bigdata - %i bytes...)' % (remaining_bytes))
        print(len(bigdata))
        lost_bytes = need_to_recieve - len(bigdata)
        print('Lost %i bytes' % (lost_bytes))
        self.conn.close()

    def generate_length_packet(self, length):
        ''' Generates a packet that indicates the next packet length '''
        length_pack = bytearray(b'\x80\x00\x00')
        length_pack.append(length)
        return length_pack

    def int_to_4hex(self, num):
        ''' Convert int to 4 byte hex (just like 1 to 00 00 00 01) '''
        #TODO: Отредактировать, должно работать с числами, больше 255
        if (num>255):
            raise ValueError('int_to_4hex() not working with numbers which more than 255')
        data = bytearray()
        data.extend(numpy.int32(num))
        data.reverse()
        return data

class SantriParser:
    ''' Santricity parser of raw data '''

    def parse_data(self, data, command):
        ''' Receives the data as an array of bytes from the server
            and returns the required data in a readable format
        '''

if __name__ == '__main__':
    my_sm_cli = SantriClient('localhost', 2463)
    my_sm_cli.show('bigdata')
