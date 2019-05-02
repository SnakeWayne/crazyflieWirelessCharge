# -*- coding: utf-8 -*-

import cflib.crtp

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

URI = 'radio://0/10/2M/E7E7E7E7E7'

def add_callback_to_cf(uri,scf):
    cflib.crtp.init_drivers(enable_debug_driver=False)
    log_conf = LogConfig(name = uri,period_in_ms=3000)
    log_conf.add_variable('pm.vbat','float')
    scf.cf.log.add_config(log_conf)
    log_conf.data_received_cb.add_callback(get_current_battery_callback)
    log_conf.start()


def get_current_battery_callback(timestamp,data,logconf):
    print(data['pm.vbat'] * 10)

if __name__ == '__main__':
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        print('start log')
        add_callback_to_cf(URI,scf)