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
from customcflib.public_swarm import PublicSWarm
from cflib.crazyflie.swarm import CachedCfFactory

from cf_dispatch import CFDispatch
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander
from fly_attr import FlyPosture
from fly_attr import CFStatus
from fly_task import *

end_all = False

URI1 = 'radio://0/20/2M/E7E7E7E7E7'
URI2 = 'radio://0/10/2M/E7E7E7E7E7'



uris = [URI1,URI2]
switch_pair_list = {'formation': ['00', [0, 0, 0]], 'charging': ['00', [0, 0, 0]]}
CFFlyTask.set_switch_pair_list(switch_pair_list)


cf_status_lock1 = threading.Lock()
cf_status_lock2 = threading.Lock()

status1 = CFStatus(URI1, FlyPosture.flying, cf_status_lock1)
status2 = CFStatus(URI2, FlyPosture.flying, cf_status_lock2)
status_list = [status1,status2]
DuplicablePositionHlCommander.set_class_status_list(status_list)




task1 = CFFlyTask(Crazyflie(), status1, [CFTrajectoryFactory.add(CFTrajectoryFactory.arch([1,1,1],[-1,-1,1],[0,0,1]), CFTrajectoryFactory.arch([-1,-1,1],[1,1,1],[0,0,1]))])
task2 = CFFlyTask(Crazyflie(), status2, [CFTrajectoryFactory.add(CFTrajectoryFactory.arch([-1,-1,1],[1,1,1],[0,0,1]), CFTrajectoryFactory.arch([1,1,1],[-1,-1,1],[0,0,1]))])
task_list = [task1,task2]



cf_args = {
    URI1:[[task1,status1,cf_status_lock1]],
    URI2:[[task2,status2,cf_status_lock2]],
    }


def is_all_end(local_status_list):
    for status in local_status_list:
        if status.current_posture != FlyPosture.charging or status.current_posture != FlyPosture.over:
            return False
    return True


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


def is_all_end(local_status_list):
    for status in local_status_list:
        if status.current_posture != FlyPosture.charging or status.current_posture != FlyPosture.over:
            return False
    return True


def run_sequence(scf, cf_arg):
    """
    Task for one cf
    :param scf: the scf which do the task
    :param cf_arg: the dic value list, at [0] is obj CFFlyTask , at [1] is obj CFStatus
    :return: None
    """
    cf = scf.cf
    cf.param.set_value('flightmode.posSet', '1')
    cf_arg[0].set_cf_afterword(cf)
    add_callback_to_singlecf(cf.link_uri, scf, cf_arg[1])
    cf_arg[0].run()
    

if __name__ == '__main__':
 
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    factory = CachedCfFactory(rw_cache='./cache')
    with PublicSWarm(uris, factory=factory) as swarm:
        # If the copters are started in their correct positions this is
        # probably not needed. The Kalman filter will have time to converge
        # any way since it takes a while to start them all up and connect. We
        # keep the code here to illustrate how to do it.
        #swarm.parallel(reset_estimator)

        # The current values of all parameters are downloaded as a part of the
        # connections sequence. Since we have 10 copters this is clogging up
        # communication and we have to wait for it to finish before we start
        # flying.
        print('Waiting for parameters to be downloaded...')
        #swarm.parallel(wait_for_param_download)

        
        swarm.parallel(run_sequence, args_dict=cf_args)

      # We take off when the commander is create
                 
