import logging, os, time, prometheus_client
from prometheus_client import Gauge
from smart_meter_connection import SmartMeterConnection

if __name__ == '__main__':

    sm_id = os.environ['SMARTMETER_ID']
    sm_key= os.environ['SMARTMETER_PASSWORD']
    sm_dev = os.environ['SMARTMETER_DEVICE']
    sm_log_level = int(os.environ['SMARTMETER_LOGLEVEL'])
    sm_interval = int(os.environ['SMARTMETER_GET_INTERVAL'])
    sm_port = int(os.environ['PORT'])

    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=sm_log_level)
    logger = logging.getLogger('connection')

    prometheus_client.start_http_server(sm_port)

    watt_gauge = Gauge('power_consumption_watt', 'Power consumption in Watt')
    ampare_gauge_r = Gauge('power_consumption_ampare_r', 'Power consumption in Ampare(R)')
    ampare_gauge_t = Gauge('power_consumption_ampare_t', 'Power consumption in Ampare(T)')
    
    with SmartMeterConnection(sm_id, sm_key, sm_dev) as conn:
        conn.initialize_params()
        while True:
            watt_data = int(conn.get_data('watt'),16)
            if not watt_data is None:
                watt_gauge.set(watt_data)
                logger.info(f'Current power consumption(Watt): {watt_data} W')
            time.sleep(sm_interval)

            ampare_data = conn.get_data('ampare')
            ampare_data_r = int(ampare_data[0:4], 16) * 0.1
            ampare_data_t = int(ampare_data[4:8], 16) * 0.1
            if not ampare_data_r  is None:
                ampare_gauge_r.set(ampare_data_r)
                logger.info(f'Current power consumption(Ampare/R): {ampare_data_r} A')
            if not ampare_data_t  is None:
                ampare_gauge_t.set(ampare_data_t)
                logger.info(f'Current power consumption(Ampare/T): {ampare_data_t} A')
            time.sleep(sm_interval)
