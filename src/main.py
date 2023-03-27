import logging, os, time, prometheus_client
from prometheus_client import Gauge
from smart_meter_connection import SmartMeterConnection

if __name__ == '__main__':

    sm_id = os.environ.get('SMARTMETER_ID', None)
    sm_key= os.environ.get('SMARTMETER_PASSWORD', None)
    sm_dev = os.environ.get('SMARTMETER_DEVICE', '/dev/ttyUSB0')
    sm_log_level = int(os.environ.get('SMARTMETER_LOGLEVEL', 10))
    sm_interval = int(os.environ.get('SMARTMETER_GET_INTERVAL', 10))
    sm_port = int(os.environ.get('PORT', 8000))

    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=sm_log_level)
    logger = logging.getLogger('connection')

    prometheus_client.start_http_server(sm_port)

    watt_gauge = Gauge('power_consumption_watt', 'Power consumption in Watt')
    ampare_gauge_r = Gauge('power_consumption_ampare_r', 'Power consumption in Ampare(R)')
    ampare_gauge_t = Gauge('power_consumption_ampare_t', 'Power consumption in Ampare(T)')
    
    with SmartMeterConnection(sm_id, sm_key, sm_dev) as conn:
        conn.initialize_params()
        while True:
            watt_raw_data = conn.get_data('watt')
            if not watt_raw_data is None:
                watt_data = int(watt_raw_data,16)
                watt_gauge.set(watt_data)
                logger.info(f'Current power consumption(Watt): {watt_data} W')

            ampare_data = conn.get_data('ampare')
            if not ampare_data is None:
                ampare_data_r = int(ampare_data[0:4], 16) * 100
                ampare_data_t = int(ampare_data[4:8], 16) * 100
                if not ampare_data_r  is None:
                    ampare_gauge_r.set(ampare_data_r)
                    logger.info(f'Current power consumption(Ampare/R): {ampare_data_r} mA')
                if not ampare_data_t  is None:
                    ampare_gauge_t.set(ampare_data_t)
                    logger.info(f'Current power consumption(Ampare/T): {ampare_data_t} mA')
            time.sleep(sm_interval)
