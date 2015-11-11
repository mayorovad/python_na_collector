''' Тесты для na_collector '''
import binascii
import unittest
import random

import na_collector


class TestNaCollector(unittest.TestCase):
    ''' unittest.TestCase class for na_collector '''
    def setUp(self):
        self.sntcli = na_collector.SantriClient()

    def test_length_packet_size(self):
        ''' Тестирование размера сгенерированного пакета длины '''
        for i in range(0, 65535):
            request_package = (0).to_bytes(i, byteorder='big')
            length_packet = self.sntcli.generate_length_packet(request_package)
            self.assertEqual(len(length_packet), 4)

    def test_length_packet_content(self):
        ''' Тестирование содержимого сгенерированного пакета длины '''
        for i in range(0, 65535):
            request_package = (0).to_bytes(i, byteorder='big')
            length_packet = self.sntcli.generate_length_packet(request_package)
            length = int(binascii.hexlify(length_packet[-3::]), 16)
            self.assertEqual(length, i)

    def test_int_to_4hex(self):
        ''' Тестирование метода перевода int в 4-ех байтовый hex '''
        for i in range(0, 65535):
            data = self.sntcli.int_to_4hex(i)
            num = int(binascii.hexlify(data[-4::]), 16)
            self.assertEqual(num, i)

    def test_packet_generator_size(self):
        ''' Тестирование размера пакета, генерируемого по коду '''
        for i in range(0, 255):
            for j in range(0, 255):
                packet = self.sntcli.generate_packet_by_code(i, j)
                if i == 0 and j == 2:
                    self.assertEqual(len(packet), 72)
                else:
                    self.assertEqual(len(packet), 40)

    def test_packet_generator_content(self):
        ''' Тестирование генерации пакетов по коду '''
        for i in range(0, 255):
            for j in range(0, 255):
                packet = self.sntcli.generate_packet_by_code(i, j)
                code_b = int(binascii.hexlify(packet[22:23]), 16)
                code_c = int(binascii.hexlify(packet[23:24]), 16)
                self.assertEqual(code_b, i)
                self.assertEqual(code_c, j)

    def test_parse_ps(self):
        ''' Тестирование определения статуса блоков питания '''
        ps_marker = b'\x00\x00\x00\xf4\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        num = 0
        for num in range(1, 3):
            packet = bytearray()
            packet.extend((random.randint(1, 10)).to_bytes(random.randint(1, 255), byteorder='big'))
            packet.extend(ps_marker)
            packet.extend((num).to_bytes(1, byteorder='big'))
            packet.extend((0).to_bytes(12, byteorder='big'))
            for code in range(0, 7):
                packet.extend((code).to_bytes(1, byteorder='big'))
                self.sntcli.parser.parse_ps(packet)
                report = self.sntcli.parser.collector_report['PS%i STATUS' % num]
                if code == 0:
                    self.assertEqual(report, 'Unknown')
                if code == 1:
                    self.assertEqual(report, 'OK')
                if code == 2:
                    self.assertEqual(report, 'Failure')
                if code == 3:
                    self.assertEqual(report, 'Failure')
                if code == 4:
                    self.assertEqual(report, 'Failure')
                if code == 5:
                    self.assertEqual(report, 'No power')
                if code == 6:
                    self.assertEqual(report, 'Unknown')

                packet.pop()

        self.sntcli.parser.collector_report.pop('PS%i STATUS' % num)

    def test_parse_battery(self):
        ''' Тестирование определения статуса батарей '''
        battery_marker = b'\x00\x00\x00\xe4\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        num = 0
        for num in range(1, 3):
            packet = bytearray()
            packet.extend((random.randint(1, 10)).to_bytes(random.randint(1, 255), byteorder='big'))
            packet.extend(battery_marker)
            packet.extend((num).to_bytes(1, byteorder='big'))
            packet.extend((0).to_bytes(12, byteorder='big'))
            for code in range(0, 15):
                packet.extend((code).to_bytes(1, byteorder='big'))
                self.sntcli.parser.parse_battery(packet)
                report = self.sntcli.parser.collector_report['BATTERY%i STATUS' % num]
                if code == 0:
                    self.assertEqual(report, 'Unknown')
                if code == 1:
                    self.assertEqual(report, 'OK')
                if code == 2:
                    self.assertEqual(report, 'OK')
                if code == 3:
                    self.assertEqual(report, 'Expiring')
                if code == 4:
                    self.assertEqual(report, 'Failure')
                if code == 5:
                    self.assertEqual(report, 'Failure')
                if code == 12:
                    self.assertEqual(report, 'Unknown')
                if code == 13:
                    self.assertEqual(report, 'Charging')
                if code == 14:
                    self.assertEqual(report, 'Unknown')

                packet.pop()

        self.sntcli.parser.collector_report.pop('BATTERY%i STATUS' % num)

    def test_parse_sfp(self):
        ''' Тестирование определения статуса SFP '''
        sfp_marker = b'\x00\x00\x01\x48\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        num = 0
        for num in range(1, 9):
            packet = bytearray()
            packet.extend((random.randint(1, 10)).to_bytes(random.randint(1, 255), byteorder='big'))
            packet.extend(sfp_marker)
            packet.extend((num).to_bytes(1, byteorder='big'))
            packet.extend((0).to_bytes(12, byteorder='big'))
            for code in range(0, 10):
                packet.extend((code).to_bytes(1, byteorder='big'))
                self.sntcli.parser.parse_sfp(packet)
                report = self.sntcli.parser.collector_report['SFP%i STATUS' % num]
                if code == 0:
                    self.assertEqual(report, 'Unknown')
                if code == 1:
                    self.assertEqual(report, 'OK')
                if code == 2:
                    self.assertEqual(report, 'Failure')
                if code == 3:
                    self.assertEqual(report, 'Unknown')

                packet.pop()

        self.sntcli.parser.collector_report.pop('SFP%i STATUS' % num)

    def test_parse_controller(self):
        ''' Тестирование определения статуса контроллера '''
        packet = bytearray()
        packet.extend((0).to_bytes(27, byteorder='big'))
        for code in range(0, 3):
            packet.extend((code).to_bytes(1, byteorder='big'))
            self.sntcli.parser.parse_controller(packet)
            report = self.sntcli.parser.collector_report['CONTROLLER STATUS']
            if code == 0:
                self.assertEqual(report, 'Unknown')
            if code == 1:
                self.assertEqual(report, 'Main')
            if code == 2:
                self.assertEqual(report, 'Unknown')

            packet.pop()

        for code in range(31, 34):
            packet.extend((code).to_bytes(1, byteorder='big'))
            self.sntcli.parser.parse_controller(packet)
            report = self.sntcli.parser.collector_report['CONTROLLER STATUS']
            if code == 31:
                self.assertEqual(report, 'Unknown')
            if code == 32:
                self.assertEqual(report, 'Reserve')
            if code == 33:
                self.assertEqual(report, 'Unknown')

            packet.pop()

        self.sntcli.parser.collector_report.pop('CONTROLLER STATUS')

if __name__ == '__main__':
    unittest.main()
    #TODO: Тестирование определения статуса стандартных томов
    #TODO: Тестирование определения объема стандартных томов
