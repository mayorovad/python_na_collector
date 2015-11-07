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
        self.parser = SantriParser()

    @staticmethod
    def generate_session_signature():
        ''' Generates a time signature for the current session '''
        #TODO: написать здесь код для генерирования сигнатуры
        #Пока что сигнатура из рандомной сессии
        session_sign = b'\x55\x6c\x31\x77'
        return session_sign

    @staticmethod
    def generate_length_packet(request_packet):
        ''' Generates a packet that indicates the request_packet length '''
        #80 - стандартное начало байта для пакета длины в SYMBol
        length_pack = bytearray(b'\x80\x00\x00')
        length_pack.append(len(request_packet))
        return length_pack

    @staticmethod
    def int_to_4hex(num):
        ''' Convert int to 4 byte hex (just like 1 to 00 00 00 01) '''
        #TODO: Отредактировать, должно работать с числами, больше 255
        #И неплохо было бы избавиться от numpy
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
        #Восстановление структуры пакета согласно протоколу
        packet_data = bytearray()
        packet_data.extend(self.time_sign)
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(2))
        packet_data.extend(b'\x53\x69\x4d\x42')
        packet_data.extend(self.int_to_4hex(1))
        #Следующий extend должен добавлять 00 00 B C
        #в зависимости от кода пакета
        packet_data.extend(b'\x00\x00')
        packet_data.append(code_b)
        packet_data.append(code_c)
        packet_data.extend(self.int_to_4hex(40))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))

        return packet_data

    def perform(self, command):
        ''' Performs user command. If the command
            is not valid, displays a list of commands.
        '''
        if command == 'q4_data':
            request_packet = self.generate_packet_by_code(0, 40)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, 'q4_data')

        return bigdata

    def get_data(self, length_packet, request_packet):
        ''' Returns data from a server in response to a request packet '''
        conn = socket.socket()
        conn.connect((self.host, self.port))

        print('Sending length_packet (request_package length is %i)' % (len(request_packet)))
        conn.send(length_packet)
        print('Sending request_packet...')
        conn.send(request_packet)

        print('Receiving length_packet from server...')
        length_packet = conn.recv(4)

        #Смотрим пакет длины от сервера, оцениваем, сколько байт будем получать
        need_to_recieve = int(binascii.hexlify(length_packet[-2::]), 16)
        remaining_bytes = need_to_recieve
        print('Server will send %i bytes' % (need_to_recieve))

        #Начинаем получать основные данные от сервера
        data = b''
        data_part_size = 4096 #Пакеты какого размера будем получать
        while remaining_bytes > 0:
            #percent = (need_to_recieve - remaining_bytes)*100/need_to_recieve
            if remaining_bytes < data_part_size-1:
                tmp = conn.recv(remaining_bytes)
                remaining_bytes -= remaining_bytes
                data += tmp
            else:
                tmp = conn.recv(data_part_size)
                remaining_bytes -= data_part_size
                data += tmp

        lost_bytes = need_to_recieve - len(data)
        print('done')
        print('Received %i bytes. %i bytes lost.' %(len(data), lost_bytes))
        conn.close()
        return data

class SantriParser:
    ''' Santricity parser of raw data'''

    def parse_data(self, data, command):
        ''' Receives the data as bytes from the server
            and returns the required information in a readable format
        '''

        #q4_data - основная информация о компонентах и томах
        if command == 'q4_data':
            print('SantriParser started with %s command' % (command))
            self.parse_battery(data)
            self.parse_sfp(data)
            self.parse_ost(data)
            self.parse_backup(data)
            self.parse_gfs(data)
            self.parse_smc(data)
            self.parse_mdt(data)
            self.parse_vm_storage(data)

    @staticmethod
    def parse_battery(data):
        ''' Parsing data for battery status '''

        battery_marker = b'\x00\x00\x00\xe4\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        position = data.find(battery_marker)
        print('Found BATTERY_MARKER on %i byte' % (position))

    @staticmethod
    def parse_sfp(data):
        ''' Parsing data for SFP status '''

        sfp_marker = b'\x00\x00\x01\x48\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        position = data.find(sfp_marker)
        print('Found SFP_MARKER on %i byte' % (position))

    @staticmethod
    def parse_ost(data):
        ''' Parsing data for OST0 volume status and capacity '''

        ost_marker = b'\x00\x00\x01\x40\x00\x00\x40\x01'
        position = data.find(ost_marker)
        print('Found OST_MARKER on %i byte' % (position))

    @staticmethod
    def parse_backup(data):
        ''' Parsing data for BACKUP volume status and capacity '''

        backup_marker = b'\x00\x00\x01\x44\x00\x00\x40\x02'
        position = data.find(backup_marker)
        print('Found BACKUP_MARKER on %i byte' % (position))

    @staticmethod
    def parse_gfs(data):
        ''' Parsing data for GFS0 volume status and capacity '''

        gfs_marker = b'\x00\x00\x01\x40\x00\x00\x40\x03'
        position = data.find(gfs_marker)
        print('Found GFS_MARKER on %i byte' % (position))

    @staticmethod
    def parse_smc(data):
        ''' Parsing data for SMCS1 volume status and capacity '''

        smc_marker = b'\x00\x00\x01\x40\x00\x00\x40\x04'
        position = data.find(smc_marker)
        print('Found SMC_MARKER on %i byte' % (position))

    @staticmethod
    def parse_mdt(data):
        ''' Parsing data for MDT0 volume status and capacity '''

        mdt_marker = b'\x00\x00\x01\x40\x00\x00\x40\x05'
        position = data.find(mdt_marker)
        print('Found MDT_MARKER on %i byte' % (position))

    @staticmethod
    def parse_vm_storage(data):
        ''' Parsing data for VM_STORAGE volume status and capacity '''

        vm_storage_marker = b'\x00\x00\x01\x4c\x00\x00\x40\x06'
        position = data.find(vm_storage_marker)
        print('Found VM_STORAGE_MARKER on %i byte' % (position))


if __name__ == '__main__':
    MY_SM_CLI = SantriClient('localhost', 2463)
    MY_SM_CLI.perform('q4_data')
