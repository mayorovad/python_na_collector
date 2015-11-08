import na_collector
import binascii
import unittest
import random

class TestNaCollector(unittest.TestCase):
    def setUp(self):
        self.sntcli = na_collector.SantriClient('localhost', 2463)

    def test_length_packet_size(self):
        ''' Тестирование размера пакета в generate_length_packet() '''
        for i in range(0, 65535):
            request_package = (0).to_bytes(i, byteorder='big')
            length_packet = self.sntcli.generate_length_packet(request_package)
            self.assertEqual(len(length_packet), 4)

    def test_length_packet_content(self):
        ''' Тестирование содержимого пакета в generate_length_packet() '''
        for i in range(0, 65535):
            request_package = (0).to_bytes(i, byteorder='big')
            length_packet = self.sntcli.generate_length_packet(request_package)
            length = int(binascii.hexlify(length_packet[-3::]), 16)
            self.assertEqual(length, i)

    def test_int_to_4hex(self):
        ''' Тестирование метода int_to_4hex() '''
        for i in range(0, 65535):
            data = self.sntcli.int_to_4hex(i)
            num = int(binascii.hexlify(data[-4::]), 16)
            self.assertEqual(num, i)

    def test_packet_generator_size(self):
        ''' Тестирование размера пакета, генерируемого
            в generate_packet_by_code()
        '''
        for i in range(0, 255):
            for j in range(0, 255):
                packet = self.sntcli.generate_packet_by_code(i, j)
                if i == 0 and j == 2:
                    self.assertEqual(len(packet), 72)
                else:
                    self.assertEqual(len(packet), 40)

    def test_packet_generator_content(self):
        ''' Тестирование содержимого пакета, генерируемого
            в generate_packet_by_code()
        '''
        for i in range(0, 255):
            for j in range(0, 255):
                packet = self.sntcli.generate_packet_by_code(i, j)
                b = int(binascii.hexlify(packet[22:23]), 16)
                c = int(binascii.hexlify(packet[23:24]), 16)
                self.assertEqual(b, i)
                self.assertEqual(c, j)

    def test_perform(self):
        ''' Проверяет, получает ли perform() нужный пакет '''
        data = self.sntcli.perform('q4_data')
        self.assertEqual(len(data), 58576)
        data = self.sntcli.perform('q1_data')
        self.assertEqual(len(data), 28)
        data = self.sntcli.perform('qpowerinfo_data')
        self.assertEqual(len(data), 72)

    def test_get_report(self):
        ''' Проверяет, возвращает ли get_report()
            нужное количество параметров
        '''
        self.sntcli.perform('q4_data')
        report = self.sntcli.get_report()
        self.assertEqual(len(report), 24)
        self.sntcli.perform('q1_data')
        report = self.sntcli.get_report()
        self.assertEqual(len(report), 25)
        self.sntcli.perform('qpowerinfo_data')
        report = self.sntcli.get_report()
        self.assertEqual(len(report), 28)

    def test_parse_ps(self):
        ps_marker = b'\x00\x00\x00\xf4\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        #генерируем пакет с требуемыми данными для обеих батареек
        packet = bytearray()
        packet.extend((random.randint(1,10)).to_bytes(random.randint(0,255), byteorder='big'))
        packet.extend(ps_marker)
        packet.extend(b'\x01')
        packet.extend((0).to_bytes(12, byteorder='big'))
        packet1 = bytearray()
        packet1.extend(packet)
        packet1.extend(b'\x01')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'OK')
        packet1.pop()
        packet1.extend(b'\x02')
        self.sntcli.parser.collector_report.pop('PS1 STATUS')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'Failure')
        packet1.pop()
        packet1.extend(b'\x03')
        self.sntcli.parser.collector_report.pop('PS1 STATUS')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'Failure')
        packet1.pop()
        packet1.extend(b'\x04')
        self.sntcli.parser.collector_report.pop('PS1 STATUS')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'Failure')
        packet1.pop()
        packet1.extend(b'\x05')
        self.sntcli.parser.collector_report.pop('PS1 STATUS')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'No power')
        packet1.pop()
        packet1.extend(b'\x06')
        self.sntcli.parser.collector_report.pop('PS1 STATUS')
        self.sntcli.parser.parse_ps(packet1)
        self.assertEqual(self.sntcli.parser.collector_report['PS1 STATUS'], 'Unknown')








if __name__ == '__main__':
	unittest.main()