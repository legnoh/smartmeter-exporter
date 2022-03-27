import logging,time
from typing import Optional, Tuple
from serial import Serial
import echonet as echonet

class SmartMeterConnection:
    def __init__(self, sm_id: str, sm_key: str, sm_dev: str):
        self.__id = sm_id
        self.__key = sm_key
        self.__dev = sm_dev
        self.__serial_logger = logging.getLogger('connection')
        self.__logger = logging.getLogger(__name__)
        self.__connection: Optional[Serial] = None
        self.__link_local_addr: Optional[str] = None

    def connect(self):
        self.__connection = Serial(self.__dev, 115200)

    def close(self):
        self.__connection.close()
        self.__connection = None

    def initialize_params(self):
        if not self.__connection:
            raise Exception('Connection is not initialized')
        version = self.__check_version()
        self.__logger.info(f'Version: {version}')
        self.__set_password(self.__key)
        self.__set_id(self.__id)
        channel, pan_id, addr = self.__scan()
        self.__logger.info(f'Channel: {channel}, Pan ID: {pan_id}, Addr; {addr}')
        self.__set_reg('S2', channel)
        self.__set_reg('S3', pan_id)
        link_local_addr = self.__get_ip_from_mac(addr)
        self.__logger.info(f'IPv6 Link Local: {link_local_addr}')
        self.__connect(link_local_addr)
        self.__logger.info(f'Connected to {link_local_addr} !')
        self.__link_local_addr = link_local_addr

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __write_line_serial(self, line: str) -> None:
        self.__serial_logger.debug(f'Send: {line}')
        self.__connection.write((line + '\r\n').encode('utf-8'))
        self.__serial_logger.debug('Echo back: ' + str(self.__connection.readline()))

    def __send_udp_serial(self, addr: str, data: bytes) -> None:
        
        head = f'SKSENDTO 1 {addr} 0E1A 1 0 {len(data):04X} '
        data = head.encode('ascii') + data
        self.__serial_logger.debug(b'Send: ' + data)
        self.__connection.write(data)
        echo_back = self.__connection.readline()
        while echo_back != head.encode('ascii') + b'\r\n':
            if echo_back != b'':
                self.__serial_logger.debug('Received Different: ' + str(echo_back))
            echo_back = self.__connection.readline()
        self.__serial_logger.debug('Echo back: ' + str(echo_back))

    def __read_line_serial(self) -> str:
        blob = b''
        blank_counter = 0
        while blob == b'':
            blank_counter += 1
            blob = self.__connection.readline()
            if blank_counter > 100:
                self.__logger.debug(f'Blank line limit exceeded. retry...')
                return ""
            text = blob.decode(encoding='utf-8')[:-2]
            self.__serial_logger.debug(f'Receive: {text}')
        return text

    def __check_version(self) -> str:
        self.__write_line_serial('SKVER')
        ever = self.__read_line_serial()
        self.__read_line_serial()
        ret = ever.split(' ', 2)
        return ret[1]

    def __set_password(self, key: str):
        self.__write_line_serial(f'SKSETPWD C {key}')
        assert self.__read_line_serial() == 'OK'

    def __set_id(self, rb_id: str):
        self.__write_line_serial(f'SKSETRBID {rb_id}')
        assert self.__read_line_serial() == 'OK'

    def __scan(self) -> Tuple[str, str, str]:
        for duration in range(4, 10):
            self.__logger.debug(f'Start scanning with duration {duration}')
            self.__write_line_serial(f'SKSCAN 2 FFFFFFFF {duration} 0')
            scan_res = {}
            while True:
                line = self.__read_line_serial()
                if line.startswith('EVENT 22'):
                    if 'Channel' not in scan_res or 'Pan ID' not in scan_res or 'Addr' not in scan_res:
                        break

                    channel = scan_res['Channel']
                    pan_id = scan_res['Pan ID']
                    addr = scan_res['Addr']
                    return channel, pan_id, addr
                elif line.startswith('  '):
                    cols = line.strip().split(':')
                    scan_res[cols[0]] = cols[1]
        raise Exception('Scan Failed')

    def __set_reg(self, reg_name: str, value: str) -> None:
        self.__write_line_serial(f'SKSREG {reg_name} {value}')
        assert self.__read_line_serial() == 'OK'

    def __get_ip_from_mac(self, addr: str) -> str:
        self.__write_line_serial(f'SKLL64 {addr}')
        return self.__read_line_serial()

    def __connect(self, addr: str) -> None:
        self.__write_line_serial(f'SKJOIN {addr}')
        while True:
            line = self.__read_line_serial()
            if line.startswith('EVENT 24'):
                raise RuntimeError('Failed to connect !')
            elif line.startswith('EVENT 25'):
                self.__read_line_serial()
                self.__connection.timeout = 1
                return
    
    def __parse_erxudp(self, event: str) -> dict[str,any]:

        erxudp_response = {}

        if not event.startswith('ERXUDP'):
            self.__logger.warn(f'this line not include ERXUDP')
            return {}

        parts = event.split(' ')
        if len(parts) == 10:
            erxudp_response = {
                'sender': parts[1],
                'dest': parts[2],
                'rport': parts[3],
                'lport': parts[4],
                'sender_lla': parts[5],
                'secured': parts[6],
                'side': parts[7],
                'datalen': int(parts[8],16),
                'data': parts[9]
            }
        elif len(parts) == 11:
            erxudp_response = {
                'sender': parts[1],
                'dest': parts[2],
                'rport': parts[3],
                'lport': parts[4],
                'sender_lla': parts[5],
                'rssi': parts[6],
                'secured': parts[7],
                'side': parts[8],
                'datalen': int(parts[9],16),
                'data': parts[10],
            }
        return erxudp_response

    def get_data(self, epc_type: str) -> Optional[int]:
        if not self.__connection:
            raise Exception('Connection is not initialized')
        if not self.__link_local_addr:
            raise Exception('Destination address is not set')
        
        if epc_type == 'watt':
            epc = echonet.epc_watt
        elif epc_type == 'ampare':
            epc = echonet.epc_ampare
        else:
            return None

        request_bytes = echonet.make_elite_request_str(epc_type)
        self.__send_udp_serial(self.__link_local_addr, request_bytes)

        if not self.__read_line_serial().startswith('EVENT 21'):
            return None
        if self.__read_line_serial() != 'OK':
            return None
        event = self.__read_line_serial()

        if event.startswith('ERXUDP'):
            parts = self.__parse_erxudp(event)
            data = echonet.parse_elite_response_data(parts['data'])
            if (    data['seoj'] == echonet.smartmeter_eoj
                and data['esv'] == echonet.esv_res_codes['Get_Res']
                and data['epc'] == epc):
                return data['edt']
        return None
