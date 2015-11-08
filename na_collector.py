''' Santricity diagnostic info collector '''
#Чтобы избавиться от бага pylint с поиском numpy

from __future__ import print_function
import socket
import binascii

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
        #Пока что сигнатура из рандомной сессии
        session_sign = b'\x55\x6c\x31\x77'
        return session_sign

    @staticmethod
    def generate_length_packet(request_packet):
        ''' Generates a packet that indicates the request_packet length '''
        #80 - стандартное начало байта для пакета длины в SYMBol
        length_pack = bytearray(b'\x80')
        length = len(request_packet)
        #to_bytes() создает массив bytes() размером 3 байта, с порядком big
        length_pack.extend(length.to_bytes(3, byteorder='big'))

        return length_pack

    @staticmethod
    def int_to_4hex(num):
        ''' Convert int to 4 hex bytes with big byte order '''
        #to_bytes() создает массив bytes() размером 4 байта, с порядком big
        #то есть сначала нулевые байты, а потом байты со значениями
        data = bytearray()
        data = num.to_bytes(4, byteorder='big')

        return data

    def generate_packet_by_code(self, code_b, code_c):
        ''' Generates the package on the signature of the session
            and the request code
        '''
        #Восстановление структуры пакета согласно протоколу
        #(см. /statistics/about_packet_structure.md)
        packet_data = bytearray()
        packet_data.extend(self.time_sign)
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(2))
        packet_data.extend(b'\x53\x69\x4d\x42')
        packet_data.extend(self.int_to_4hex(1))
        #Следующие 3 extend должны добавлять 00 00 B C
        packet_data.extend(b'\x00\x00')
        packet_data.append(code_b)
        packet_data.append(code_c)
        packet_data.extend(self.int_to_4hex(40))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))

        #Дополнительные 32 байта для q1, зачем нужны - не знаю
        if code_b == 0 and code_c == 2:
            packet_data.extend(b'\x07\x00\x00\x00')
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(self.int_to_4hex(1))
            packet_data.extend(self.int_to_4hex(16))
            packet_data.extend(b'\x60\x0a\x09\x80')
            packet_data.extend(b'\x00\x5d\xe4\x9d')
            packet_data.extend(self.int_to_4hex(0))
            packet_data.extend(b'\x53\xd8\x64\x0f')

        return packet_data

    def perform(self, command):
        ''' Performs user command. If the command
            is not valid, displays a list of commands.
        '''
        print('\n***Performing %s command***' % command)
        #q4_data - основная информация о компонентах и томах
        if command == 'q4_data':
            request_packet = self.generate_packet_by_code(0, 40)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        #q1_data - информация о режиме контроллера
        if command == 'q1_data':
            request_packet = self.generate_packet_by_code(0, 2)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        #qpowerinfo_data - информация о блоках питания
        if command == 'qpowerinfo_data':
            request_packet = self.generate_packet_by_code(2, 202)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        return bigdata

    def get_data(self, length_packet, request_packet):
        ''' Returns data from a server in response to a request packet '''
        print('Connecting to %s:%i...' % (self.host, self.port), end='')
        conn = socket.socket()
        conn.connect((self.host, self.port))
        print('done')

        print('Sending request to server...', end='')
        conn.send(length_packet)
        conn.send(request_packet)
        print('done')

        print('Receiving data from server...', end='')
        length_packet = conn.recv(4)

        #Смотрим пакет длины от сервера, оцениваем, сколько байт будем получать
        need_to_recieve = int(binascii.hexlify(length_packet[-2::]), 16)
        remaining_bytes = need_to_recieve

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

    def get_report(self):
        ''' Return report from parser '''
        return self.parser.collector_report

class SantriParser:
    ''' Santricity parser of raw data'''

    def __init__(self):
        self.collector_report = {}

    def parse_data(self, data, command):
        ''' Receives the data as bytes from the server
            and returns the required information in a readable format
        '''

        #q4_data - основная информация о компонентах и томах
        if command == 'q4_data':
            print('\n***SantriParser started with %s command***' % (command))
            self.parse_ps(data)
            self.parse_battery(data)
            self.parse_sfp(data)
            self.parse_ost(data)
            self.parse_backup(data)
            self.parse_gfs(data)
            self.parse_smc(data)
            self.parse_mdt(data)
            self.parse_vm_storage(data)
        #q1_data - информация о режиме контроллера
        if command == 'q1_data':
            print('\n***SantriParser started with %s command***' % (command))
            self.parse_controller(data)
        #qpowerinfo_data - информация о блоках питания
        if command == 'qpowerinfo_data':
            print('\n***SantriParser started with %s command***' % (command))
            self.parse_voltage(data)

    def parse_ps(self, data):
        ''' Parsing data for power supply status '''
        #marker -> battery_num (1 byte) -> 12 null bytes -> sence_byte (sign char)
        ps_marker = b'\x00\x00\x00\xf4\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        position = data.find(ps_marker + b'\x01')
        status = data[position + len(ps_marker) + 1 + 12]
        if status == 1:
            self.collector_report['PS1 STATUS'] = 'OK'
        else:
            if status in range(2, 4):
                self.collector_report['PS1 STATUS'] = 'Failure'
            else:
                if status == 5:
                    self.collector_report['PS1 STATUS'] = 'No power'
                else:
                    self.collector_report['PS1 STATUS'] = 'Unknown'

        print('Power supply 1 status is %i' % status)
        position = data.find(ps_marker + b'\x02')
        status = data[position + len(ps_marker) + 1 + 12]
        if status == 1:
            self.collector_report['PS2 STATUS'] = 'OK'
        else:
            if status in range(2, 4):
                self.collector_report['PS2 STATUS'] = 'Failure'
            else:
                if status == 5:
                    self.collector_report['PS2 STATUS'] = 'No power'
                else:
                    self.collector_report['PS2 STATUS'] = 'Unknown'
        print('Power supply 2 status is %i' % status)

    def parse_battery(self, data):
        ''' Parsing data for battery status '''
        #marker -> battery_num (1 byte) -> 12 null bytes -> sence_byte (sign char)
        battery_marker = b'\x00\x00\x00\xe4\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        position = data.find(battery_marker + b'\x01')
        status = data[position + len(battery_marker) + 1 + 12]
        if status in range(1, 2):
            self.collector_report['BATTERY1 STATUS'] = 'OK'
        else:
            if status == 3:
                self.collector_report['BATTERY1 STATUS'] = 'Expiring'
            else:
                if status in range(4, 5):
                    self.collector_report['BATTERY1 STATUS'] = 'Failure'
                else:
                    if status == 13:
                        self.collector_report['BATTERY1 STATUS'] = 'Charging'
                    else:
                        self.collector_report['BATTERY1 STATUS'] = 'Unknown'

        print('Battery 1 status is %i' % status)
        position = data.find(battery_marker + b'\x02')
        status = data[position + len(battery_marker) + 1 + 12]
        if status in range(1, 2):
            self.collector_report['BATTERY2 STATUS'] = 'OK'
        else:
            if status == 3:
                self.collector_report['BATTERY2 STATUS'] = 'Expiring'
            else:
                if status in range(4, 5):
                    self.collector_report['BATTERY2 STATUS'] = 'Failure'
                else:
                    if status == 13:
                        self.collector_report['BATTERY2 STATUS'] = 'Charging'
                    else:
                        self.collector_report['BATTERY2 STATUS'] = 'Unknown'
        print('Battery 2 status is %i' % status)

    def parse_sfp(self, data):
        ''' Parsing data for SFP status '''
        #marker -> sfp_num (1 byte) -> 12 null bytes -> sence_byte (sign char)
        sfp_marker = b'\x00\x00\x01\x48\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        for num in range(1, 9):
            position = data.find(sfp_marker + (num).to_bytes(1, byteorder='big'))
            status = data[position + len(sfp_marker) + 1 + 12]
            if status == 1:
                self.collector_report['SFP%i STATUS' % num] = 'OK'
            else:
                if status == 2:
                    self.collector_report['SFP%i STATUS' % num] = 'Failure'
                else:
                    self.collector_report['SFP%i STATUS' % num] = 'Unknown'
            print('SFP%i status is %i' % (num, status))

    def parse_ost(self, data):
        ''' Parsing data for OST0 volume status and capacity '''
        #marker -> 71 null bytes -> status_byte (sign char)
        #marker -> 37 null bytes -> capacity_byte (short_int - 2 bytes)
        ost_marker = b'\x00\x00\x01\x40\x00\x00\x40\x01'
        position = data.find(ost_marker)
        status = data[position + len(ost_marker) + 71]
        self.parse_volume_status(status, 'OST0')
        capacity_position = position + len(ost_marker) + 37
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['OST0 CAPACITY'] = '%i TB' % capacity
        print('OST0 status is %i, capacity is %i TB' % (status, capacity))

    def parse_backup(self, data):
        ''' Parsing data for BACKUP volume status and capacity '''
        #marker -> 75 null bytes -> status_byte (sign char)
        #marker -> 41 null bytes -> capacity_byte (short_int - 2 bytes)
        backup_marker = b'\x00\x00\x01\x44\x00\x00\x40\x02'
        position = data.find(backup_marker)
        status = data[position + len(backup_marker) + 75]
        self.parse_volume_status(status, 'BACKUP')
        capacity_position = position + len(backup_marker) + 41
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['BACKUP CAPACITY'] = '%i TB' % capacity
        print('BACKUP status is %i, capacity is %i TB' % (status, capacity))

    def parse_gfs(self, data):
        ''' Parsing data for GFS0 volume status and capacity '''
        #marker -> 71 null bytes -> status_byte (sign char)
        #marker -> 37 null bytes -> capacity_byte (short_int - 2 bytes)
        gfs_marker = b'\x00\x00\x01\x40\x00\x00\x40\x03'
        position = data.find(gfs_marker)
        status = data[position + len(gfs_marker) + 71]
        self.parse_volume_status(status, 'GFS0')
        capacity_position = position + len(gfs_marker) + 37
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['GFS0 CAPACITY'] = '%i TB' % capacity
        print('GFS0 status is %i, capacity is %i TB' % (status, capacity))

    def parse_smc(self, data):
        ''' Parsing data for SMC1 volume status and capacity '''
        #marker -> 71 null bytes -> status_byte (sign char)
        #marker -> 37 null bytes -> capacity_byte (short_int - 2 bytes)
        smc_marker = b'\x00\x00\x01\x40\x00\x00\x40\x04'
        position = data.find(smc_marker)
        status = data[position + len(smc_marker) + 71]
        self.parse_volume_status(status, 'SMC1')
        capacity_position = position + len(smc_marker) + 37
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['SMC1 CAPACITY'] = '%i TB' % capacity
        print('SMC1 status is %i, capacity is %i TB' % (status, capacity))

    def parse_mdt(self, data):
        ''' Parsing data for MDT0 volume status and capacity '''
        #marker -> 71 null bytes -> status_byte (sign char)
        #marker -> 37 null bytes -> capacity_byte (short_int - 2 bytes)
        mdt_marker = b'\x00\x00\x01\x40\x00\x00\x40\x05'
        position = data.find(mdt_marker)
        status = data[position + len(mdt_marker) + 71]
        self.parse_volume_status(status, 'MDT0')
        capacity_position = position + len(mdt_marker) + 37
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['MDT0 CAPACITY'] = '%i TB' % capacity
        print('MDT0 status is %i, capacity is %i TB' % (status, capacity))

    def parse_vm_storage(self, data):
        ''' Parsing data for VM_STORAGE volume status and capacity '''
        #marker -> 83 null bytes -> status_byte (sign char)
        #marker -> 49 null bytes -> capacity_byte (short_int - 2 bytes)
        vm_storage_marker = b'\x00\x00\x01\x4c\x00\x00\x40\x06'
        position = data.find(vm_storage_marker)
        status = data[position + len(vm_storage_marker) + 83]
        self.parse_volume_status(status, 'VM_STORAGE')
        capacity_position = position + len(vm_storage_marker) + 49
        capacity = int(binascii.hexlify(data[capacity_position:capacity_position+2]), 16)
        self.collector_report['VM_STORAGE CAPACITY'] = '%i TB' % capacity
        print('VM_STORAGE status is %i, capacity is %i TB' % (status, capacity))

    def parse_controller(self, data):
        ''' Parsing data for controller status '''
        #27 null bytes -> status_byte (sign char)
        status = data[27]
        if status == 1:
            self.collector_report['CONTROLLER STATUS'] = 'Main'
        else:
            if status == 32:
                self.collector_report['CONTROLLER STATUS'] = 'Reserve'
            else:
                self.collector_report['CONTROLLER STATUS'] = 'Unknown'
        print('Controller status is %i' % status)

    def parse_voltage(self, data):
        ''' Parsing data for voltage of each controller '''
        #-> 36 null bytes -> summary_voltage (long_int - 4 bytes?)
        #-> 64 null bytes -> voltage1 (long_int - 4 bytes?)
        #-> 68 null bytes -> voltage2 (long_int - 4 bytes?)
        summary_voltage = int(binascii.hexlify(data[36:36+4]), 16)
        voltage1 = int(binascii.hexlify(data[64:64+4]), 16)
        voltage2 = int(binascii.hexlify(data[68:68+4]), 16)
        self.collector_report['SUMMARY VOLTAGE'] = '%i W' % summary_voltage
        self.collector_report['PS1 VOLTAGE'] = '%i W' % voltage1
        self.collector_report['PS2 VOLTAGE'] = '%i W' % voltage2
        print('Power supply summary voltage is %i W' % summary_voltage)
        print('Power supply 1 voltage is %i W' % voltage1)
        print('Power supply 2 voltage is %i W' % voltage2)

    def parse_volume_status(self, status, volume_name):
        ''' Parsing status of standart volumes '''
        if status == 1:
            self.collector_report['%s STATUS' % volume_name] = 'OK'
        else:
            self.collector_report['%s STATUS' % volume_name] = 'Unknown'

if __name__ == '__main__':
    #XXX: эмулятор перестает отвечать после нескольких запросов
    MY_SM_CLI = SantriClient('localhost', 2463)
    MY_SM_CLI.perform('q4_data')
    MY_SM_CLI.perform('q1_data')
    MY_SM_CLI.perform('qpowerinfo_data')
    SM_REPORT = MY_SM_CLI.get_report()
    print('\n***Listing of collected data***')
    print(SM_REPORT)

