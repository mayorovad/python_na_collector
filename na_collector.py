''' Santricity diagnostic info collector '''

from __future__ import print_function
import socket
import binascii
import configparser

#TODO: Все отступы в конфиг

class SantriClient:
    ''' Santricity client that sends the packets to the server
        and transmits the response from the server to parser
    '''

    def __init__(self):
        #Инициализируем конфиг
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.host = self.config['CONNECTION']['Name']
        self.port = self.config.getint('CONNECTION', 'Port')

        self.time_sign = self.generate_time_signature()
        self.parser = SantriParser()

    def generate_time_signature(self):
        ''' Generates a time signature for the current session '''
        #Пока что сигнатура из рандомной сессии
        session_sign = binascii.unhexlify(self.config['SYMB']['TimeSignature'])

        return session_sign

    def generate_length_packet(self, request_packet):
        ''' Generates a packet that indicates the request_packet length '''
        #Получаем из конфига стандартное начало пакета длины
        length_start_raw = self.config['SYMB']['LengthPacketStart']
        length_start = binascii.unhexlify(length_start_raw)

        length = len(request_packet)
        #to_bytes() создает массив bytes() размером 3 байта, с порядком big
        length_pack = length_start + length.to_bytes(3, byteorder='big')
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
        #см. в docs/about_packet_structure.md
        packet_data = bytearray()
        packet_data.extend(self.time_sign)
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(2))

        symb_sign_raw = self.config['SYMB']['SymbSignature']
        symb_sign = binascii.unhexlify(symb_sign_raw)
        packet_data += symb_sign

        packet_data.extend(self.int_to_4hex(1))
        #Следующие 3 extend должны добавлять 00 00 B C
        packet_data += (0).to_bytes(2, byteorder='big')
        packet_data.append(code_b)
        packet_data.append(code_c)
        packet_data.extend(self.int_to_4hex(40))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        packet_data.extend(self.int_to_4hex(0))
        #Дополнительные 32 байта для q1, зачем нужны - не знаю
        if code_b == 0 and code_c == 2:
            q1_last_bytes_raw = self.config['SYMB']['Q1LastBytes']
            packet_data += binascii.unhexlify(q1_last_bytes_raw)
        return packet_data

    def perform(self, command):
        ''' Performs user command. If the command
            is not valid, displays a list of commands.
        '''

        if command == 'q4_data':
            #q4_data - основная информация о компонентах и томах
            print('\n***Performing %s command***' % command)
            request_packet = self.generate_packet_by_code(0, 40)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        if command == 'q1_data':
            #q1_data - информация о режиме контроллера
            print('\n***Performing %s command***' % command)
            request_packet = self.generate_packet_by_code(0, 2)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        if command == 'qpowerinfo_data':
            #qpowerinfo_data - информация о блоках питания
            print('\n***Performing %s command***' % command)
            request_packet = self.generate_packet_by_code(2, 202)
            length_packet = self.generate_length_packet(request_packet)
            bigdata = self.get_data(length_packet, request_packet)
            self.parser.parse_data(bigdata, command)

        if command not in ['qpowerinfo_data', 'q4_data', 'q1_data']:
            print('\nWARNING: The command %s is not valid' % command)
            print('q1_data - controller status')
            print('q4_data - diagnostic information')
            print('qpowerinfo_data - power consumption info')

    def get_data(self, length_packet, request_packet):
        ''' Returns data from a server in response to a request packet '''
        print('Connecting to %s:%i...' % (self.host, self.port), end='')
        conn = socket.socket()
        conn.connect((self.host, self.port))
        print('done')

        #TODO Давай сделаем отдельную функцию, которая будет отправлять запрос
        #     на сервер и возвращать need_to_recieve
        print('Sending request to server...', end='')
        conn.send(length_packet)
        conn.send(request_packet)
        print('done')

        print('Receiving data from server...', end='')
        length_packet = conn.recv(4)

        #Смотрим пакет длины от сервера, оцениваем, сколько байт будем получать
        need_to_recieve = int(binascii.hexlify(length_packet[-3::]), 16)
        remaining_bytes = need_to_recieve

        #Начинаем получать данные от сервера
        data = b''
        #Пакеты какого размера будем получать
        data_part_size = self.config.getint('CONNECTION', 'DataPartSize')

        while remaining_bytes > 0:
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
        #Инициализируем конфиг
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
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
            self.parse_power(data)

        if command not in ['qpowerinfo_data', 'q4_data', 'q1_data']:
            print('\nWARNING: The command %s is not valid' % command)
            print('q1_data - controller status')
            print('q4_data - diagnostic information')
            print('qpowerinfo_data - power consumption info')

    def parse_ps(self, data):
        ''' Parsing data for power supply status '''
        #marker -> battery_num (1 byte) -> 12 null bytes -> sence_byte (sign char)

        ps_marker_raw = self.config['MARKER']['PowerSupply']
        ps_marker = binascii.unhexlify(ps_marker_raw)

        position = data.find(ps_marker + b'\x01')
        status = data[position + len(ps_marker) + 1 + 12]
        if status == 1:
            self.collector_report['PS1 STATUS'] = 'OK'
        else:
            if status in range(2, 5):
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
            if status in range(2, 5):
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

        battery_marker_raw = self.config['MARKER']['Battery']
        battery_marker = binascii.unhexlify(battery_marker_raw)

        position = data.find(battery_marker + b'\x01')
        status = data[position + len(battery_marker) + 1 + 12]
        if status in range(1, 3):
            self.collector_report['BATTERY1 STATUS'] = 'OK'
        else:
            if status == 3:
                self.collector_report['BATTERY1 STATUS'] = 'Expiring'
            else:
                if status in range(4, 6):
                    self.collector_report['BATTERY1 STATUS'] = 'Failure'
                else:
                    if status == 13:
                        self.collector_report['BATTERY1 STATUS'] = 'Charging'
                    else:
                        self.collector_report['BATTERY1 STATUS'] = 'Unknown'

        print('Battery 1 status is %i' % status)
        position = data.find(battery_marker + b'\x02')
        status = data[position + len(battery_marker) + 1 + 12]
        if status in range(1, 3):
            self.collector_report['BATTERY2 STATUS'] = 'OK'
        else:
            if status == 3:
                self.collector_report['BATTERY2 STATUS'] = 'Expiring'
            else:
                if status in range(4, 6):
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

        sfp_marker_raw = self.config['MARKER']['SFP']
        sfp_marker = binascii.unhexlify(sfp_marker_raw)

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

        ost_marker_raw = self.config['MARKER']['OST0']
        ost_marker = binascii.unhexlify(ost_marker_raw)

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

        backup_marker_raw = self.config['MARKER']['BACKUP']
        backup_marker = binascii.unhexlify(backup_marker_raw)

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

        gfs_marker_raw = self.config['MARKER']['GFS0']
        gfs_marker = binascii.unhexlify(gfs_marker_raw)

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

        smc_marker_raw = self.config['MARKER']['SMC1']
        smc_marker = binascii.unhexlify(smc_marker_raw)

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

        mdt_marker_raw = self.config['MARKER']['MDT0']
        mdt_marker = binascii.unhexlify(mdt_marker_raw)

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

        vm_storage_marker_raw = self.config['MARKER']['VM_STORAGE']
        vm_storage_marker = binascii.unhexlify(vm_storage_marker_raw)

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

    def parse_power(self, data):
        ''' Parsing data for power of each controller '''
        #-> 36 null bytes -> summary_voltage (long_int - 4 bytes?)
        #-> 64 null bytes -> voltage1 (long_int - 4 bytes?)
        #-> 68 null bytes -> voltage2 (long_int - 4 bytes?)
        summary_voltage = int(binascii.hexlify(data[36:36+4]), 16)
        voltage1 = int(binascii.hexlify(data[64:64+4]), 16)
        voltage2 = int(binascii.hexlify(data[68:68+4]), 16)
        self.collector_report['SUMMARY WATT'] = '%i W' % summary_voltage
        self.collector_report['PS1 WATT'] = '%i W' % voltage1
        self.collector_report['PS2 WATT'] = '%i W' % voltage2
        print('Power supply summary power is %i W' % summary_voltage)
        print('Power supply 1 power is %i W' % voltage1)
        print('Power supply 2 power is %i W' % voltage2)

    def parse_volume_status(self, status, volume_name):
        ''' Parsing status of standart volumes '''
        if status == 1:
            self.collector_report['%s STATUS' % volume_name] = 'OK'
        else:
            self.collector_report['%s STATUS' % volume_name] = 'Unknown'

if __name__ == '__main__':
    #Откючаю сообщения pylint о константах
    # pylint: disable=C0103
    santri_client = SantriClient()
    santri_client.perform('q4_data')
    santri_client.perform('q1_data')
    santri_client.perform('qpowerinfo_data')
    santri_client.perform('do_a_barrel_roll')
    santri_report = santri_client.get_report()
    print('\n***Listing of collected data***')
    print(santri_report)
    # pylint: enable=C0103

