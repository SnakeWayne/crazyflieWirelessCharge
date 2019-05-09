import cflib.crtp
import time
import logging
import threading


from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

from cflib.crazyflie import Crazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.positioning.position_hl_commander import PositionHlCommander
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander
from fly_attr import FlyPosture
from fly_attr import CFStatus
from fly_task import *


URI = 'radio://0/20/2M/E7E7E7E7E7'



def position_callback(timestamp, data, logconf):
    pass
def update_cfstatus(timestamp, data, logconf, status, uri):
    status.current_position[0] = data['kalman.stateX'] 
    status.current_position[1] = data['kalman.stateY'] 
    status.current_position[2] = data['kalman.stateZ']
    status.current_battery = data['pm.vbat'] * 10
    #print(uri,'x:', status.current_position[0],'y:', status.current_position[1],'z:', status.current_position[2])

def add_callback_to_singlecf(uri, scf, status):
    cflib.crtp.init_drivers(enable_debug_driver=False)
    log_conf = LogConfig(name=uri, period_in_ms=500)
    log_conf.add_variable('kalman.stateX', 'float')
    log_conf.add_variable('kalman.stateY', 'float')
    log_conf.add_variable('kalman.stateZ', 'float')
    log_conf.add_variable('pm.vbat', 'float')
    scf.cf.log.add_config(log_conf)

    def outer_callback(timestamp, data, logconf):
        return update_cfstatus(timestamp, data, logconf, status, uri)
    log_conf.data_received_cb.add_callback(outer_callback)
    print('about to start log')
    log_conf.start()
if __name__ == '__main__':
    switch_pair_list = {'formation': ['00', [0, 0, 0]], 'charging': ['00', [0, 0, 0]]}  
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    cf_status_lock1 = threading.Lock()
# cf_status_lock3 = threading.Lock()  # 访问status.current_posture时所需要的锁

# CFStatus, in the final version we may use a list to store it
    status1 = CFStatus(URI, FlyPosture.flying, cf_status_lock1)
    status_list = [status1]
    CFFlyTask.set_switch_pair_list(switch_pair_list)
    task1 = CFFlyTask(Crazyflie(), status1, [CFTrajectoryFactory.arch([1,1,1],[-1,-1,1],[-1,1,0]),CFTrajectoryFactory.arch([-1,-1,1],[1,1,1],[-1,1,0])])
    DuplicablePositionHlCommander.set_class_status_list(status_list)
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        task1.set_cf_afterword(scf.cf)
        add_callback_to_singlecf(URI,scf,status1)
        task1.run()
      # We take off when the commander is create
                 
