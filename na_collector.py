''' Santricity diagnostic info collector '''
#Чтобы избавиться от бага pylint с поиском numpy

from __future__ import print_function
import socket
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

    @staticmethod
    def generate_session_signature():
        ''' Generates a time signature for the current session '''
        #TODO: написать код для генерирования сигнатуры
        #Пока что сигнатура из рандомной сессии
        session_sign = b'\x55\x6c\x31\x77'
        return session_sign

    @staticmethod
    def generate_length_packet(length):
        ''' Generates a packet that indicates the next packet length '''
        length_pack = bytearray(b'\x80\x00\x00')
        length_pack.append(length)
        return length_pack

    @staticmethod
    def int_to_4hex(num):
        ''' Convert int to 4 byte hex (just like 1 to 00 00 00 01) '''
        #TODO: Отредактировать, должно работать с числами, больше 255
        if num > 255:
            raise ValueError('int_to_4hex() not working with numbers which more than 255')
        data = bytearray()
        data.extend(numpy.int32(num))
        data.reverse()
        return data

    def generate_packet_by_code(self, code_b, code_c):
        ''' Generates the package on the signature of the session
            and the request code
        '''

        packet_data = bytearray()

        packet_data.extend(self.time_sign)
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(2))
        packet_data.extend(b'\x53\x69\x4d\x42')
        packet_data.extend(self.int_to_4hex(1))
        #Следующий extend должен добавлять 00 00 B C
        #В зависимости от кода пакета
        packet_data.extend(b'\x00\x00')
        packet_data.append(code_b)
        packet_data.append(code_c)
        packet_data.extend(self.int_to_4hex(40))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))

        return packet_data

    def show(self, command):
        ''' Gets the server's response to the command '''
        if command == 'bigdata':
            request_packet = self.generate_packet_by_code(0, 40)
            bigdata = self.get_data(request_packet)
        return bigdata

    def get_data(self, request_package):
        ''' Returns data from a server in response to a request packet '''
        conn = socket.socket()
        conn.connect((self.host, self.port))

        #Делим на 2, так как нужна длина в байтах
        length_packet = self.generate_length_packet(len(request_package))

        print('Sending length_packet (request_package length is %i)' % (len(request_package)))
        conn.send(length_packet)
        print('Sending request_package...')
        conn.send(request_package)

        print('Receiving length_packet from server...')
        length_packet = conn.recv(4)
        need_to_recieve = int(binascii.hexlify(length_packet[-2::]), 16)
        remaining_bytes = need_to_recieve
        print('Server will send %i bytes' % (need_to_recieve))

        bigdata = b''
        tmp = conn.recv(1)
        remaining_bytes -= 1
        bigdata += tmp
        while remaining_bytes > 0:
            percent = (need_to_recieve - remaining_bytes)*100/need_to_recieve
            #print('%i%% ' % (percent), end="", flush=True)
            if remaining_bytes < 2:
                tmp = conn.recv(remaining_bytes)
                remaining_bytes -= remaining_bytes
                bigdata += tmp
            else:
                tmp = conn.recv(2)
                print(binascii.hexlify(tmp))
                if binascii.hexlify(tmp)==b'e409':
                    print('FOUND E409')
                    break
                remaining_bytes -= 2
                bigdata += tmp

        lost_bytes = need_to_recieve - len(bigdata)
        print('done')
        print('Received %i bytes. %i bytes lost.' %(len(bigdata), lost_bytes))
        conn.close()
        return bigdata

class SantriParser:
    ''' Santricity parser of raw data '''

    def parse_data(self, data, command):
        ''' Receives the data as an array of bytes from the server
            and returns the required data in a readable format
        '''


if __name__ == '__main__':
    MY_SM_CLI = SantriClient('localhost', 2463)
    bigdata = MY_SM_CLI.show('bigdata')
    #print(binascii.hexlify(bigdata))
    print('\n main: bigdata output completed')
    MY_SM_PARSER = SantriParser()
    MY_SM_PARSER.parse_data(bigdata, 'bigdata')