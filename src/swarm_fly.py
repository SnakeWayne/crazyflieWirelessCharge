# -*- coding: utf-8 -*-
"""
The main function to control multi cf to fly and then dynamic change cf to charge

"""
import time
import threading

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.__init__ import Crazyflie

from cf_dispatch import CFDispatch
from fly_task import CFTrajectoryFactory
from fly_task import CFFlyTask
from customcflib.public_swarm import PublicSWarm
from fly_attr import FlyPosture
from fly_control import CFCollisionAvoidance
from fly_attr import CFSequence
from fly_attr import CFStatus
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander


# Change uris and sequences according to your setup
URI1 = 'radio://0/10/2M/E7E7E7E7E7'
URI2 = 'radio://0/00/2M/E7E7E7E7E7'
URI3 = 'radio://0/40/2M/E7E7E7E7E7'
URI4 = 'radio://0/60/2M/E7E7E7E7E7'

end_all = False

# CFSequences, in the final version we may use a list to store it
sequence1 = CFSequence([
[0.5, 0.5, 0.5,2],
[0.5, 0.5, 1,2],
[0.5, 0.5, 1,2],
[0.5, 0.5, 0.5,2],
[0.5, 0.5, 1,2],
[0.5, 0.5, 0.5,2],
[0.5, 0.5, 1,2],
])  # temp
sequence2 = CFSequence([
[0, 0, 0.5,2],
[0, 0, 1,2],
[0, 0, 1,2],
[0, 0, 0.5,2],
[0, 0, 1,2],
[0, 0, 0.5,2],
[0, 0, 1,2],
])  # temp

cf_status_lock1 = threading.Lock()
cf_status_lock2 = threading.Lock()
# cf_status_lock3 = threading.Lock()  # 访问status.current_posture时所需要的锁

# CFStatus, in the final version we may use a list to store it
status1 = CFStatus(URI1, FlyPosture.flying, cf_status_lock1)  # temp
status2 = CFStatus(URI2, FlyPosture.flying, cf_status_lock2)  # temp

status_list = [status1, status2]  # temp
#  status3 = CFStatus(URI3, FlyPosture.charging, cf_status_lock3)  # temp

task1 = CFFlyTask(Crazyflie(), status1, [CFTrajectoryFactory.line([0,0,1],[1,1,1])])
task2 = CFFlyTask(Crazyflie(), status2, [CFTrajectoryFactory.line([1,1,1],[0,0,1])])

task_list = [task1, task2]  # temp

switch_pair_list = {'formation': ['00', [0, 0, 0]], 'charging': ['00', [0, 0, 0]]}  # 主线程在判断产生充电无人机时需要调度的无人机的信息位，
# 被CFFlyTask当作静态成员供所有无人机查找

DuplicablePositionHlCommander.set_class_status_list(status_list)
CFFlyTask.set_switch_pair_list(switch_pair_list)

# used to pass param to the parallel thread
cf_args = {
    URI1: [[task1, status1, cf_status_lock1]],
    URI2: [[task2, status2, cf_status_lock2]],
    }

# List of URIs, comment the one you do not want to fly
uris = {
    URI1,
    URI2,
}

# Dict of scfs
scfs = []


#def renew_all_task_cf(local_task_list, local_scf_list):  # 由于cf无法在初始化时定义，只能通过初始化占位后再修改去做
#    for i in range(len(local_task_list)):
#        local_task_list[i].set_cf_afterword(local_scf_list[i].cf)


def get_status_from_status_list(uri, local_status_list):
    def condition(status): return status.uri == uri
    result = list(filter(condition, local_status_list))
    if len(result) == 0:
        return None
    return result[0]


def get_sequence_from_sequence_list(uri, local_sequence_list):
    def condition(sequence): return sequence.uri == uri
    result = list(filter(condition, local_sequence_list))
    if len(result) == 0:
        return None
    return result[0]


def wait_for_position_estimator(scf):
    print('Waiting for estimator to find position...')

    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.stateX', 'float')
    log_config.add_variable('kalman.stateY', 'float')
    log_config.add_variable('kalman.stateZ', 'float')

    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]
            log_config.add_variable('ranging.distance2', 'float')
            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break


def wait_for_param_download(scf):
    while not scf.cf.param.is_updated:
        time.sleep(1.0)
    print('Parameters downloaded for', scf.cf.link_uri)


def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')

    wait_for_position_estimator(cf)


def take_off(cf, position):
    take_off_time = 1.0
    sleep_time = 0.1
    steps = int(take_off_time / sleep_time)
    vz = position[2] / take_off_time

    print(vz)

    for i in range(steps):
        cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
        time.sleep(sleep_time)


def land(cf, position):
    landing_time = 1.0
    sleep_time = 0.1
    steps = int(landing_time / sleep_time)
    vz = -position[2] / landing_time

    print(vz)

    for i in range(steps):
        cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
        time.sleep(sleep_time)

    cf.commander.send_setpoint(0, 0, 0, 0)
    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)

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
    try:
        cf = scf.cf
        cf.param.set_value('flightmode.posSet', '1')
        cf_arg[0].set_cf_afterword(cf)
        CFDispatch.add_callback_to_singlecf(cf.link_uri, scf, cf_arg)
        global status_list
        global end_all
        for sta in status_list:
            print(sta.current_position)
        #if cf_arg[1].current_posture == FlyPosture.flying:
         #     flying_cf_avoidance = CFCollisionAvoidance(cf, cf_arg[1])
          #    flying_cf_avoidance.start_avoid(status_list)
        print(cf.link_uri,'enter cf thread while true')
        while True:
            if end_all:
                break
            if is_all_end(status_list):
                break
            if cf_arg[1].current_posture == FlyPosture.flying:
                print(cf.link_uri,'is going to run')
                cf_arg[0].run()
            elif cf_arg[1].current_posture == FlyPosture.charging:
                time.sleep(5)
            elif cf_arg[1].current_posture == FlyPosture.over:
                break
    except Exception as e:
        print(e)


def global_dispatch():
    global cf_args
    global status_list
    global scfs
    global end_all
    while True:
        try:
            time.sleep(10)
            formation_cf_uri, charging_cf_uri = CFDispatch.calculate_how_to_dispatch(status_list)

            if formation_cf_uri == 'radio':  # temp define invalid uri
                continue
            elif formation_cf_uri == 'abort':
                print('we should land')  # fly control need
                # tell every one to land, maybe set the current sequence to max for all
            else:
                print('switching')
                formation_cf = scfs[formation_cf_uri].cf
                charging_cf = scfs[charging_cf_uri].cf
                switch_pair_list['formation'][0] = formation_cf_uri
                formation_status = get_status_from_status_list(formation_cf_uri, status_list)
                switch_pair_list['formation'][1][0] = formation_status.current_position[0]
                switch_pair_list['formation'][1][1] = formation_status.current_position[1]
                switch_pair_list['formation'][1][2] = formation_status.current_position[2]
                switch_pair_list['charging'][0] = charging_cf_uri
                charging_status = get_status_from_status_list(charging_cf_uri,status_list)
                switch_pair_list['charging'][1][0] = charging_status.current_position[0]
                switch_pair_list['charging'][1][1] = charging_status.current_position[1]
                switch_pair_list['charging'][1][2] = charging_status.current_position[2]
                commander = DuplicablePositionHlCommander(charging_cf)
                commander.take_off()
                while formation_status.current_posture != FlyPosture.charging:
                    time.sleep(0.1)
                print('formation cf has land')
                cf_args[charging_cf_uri][0].copy(cf_args[formation_cf_uri][0])
                with charging_status.status_lock:  # 更新充电无人机状态，在无人机线程中可以唤醒
                    charging_status.current_posture = FlyPosture.flying
                    charging_cf_avoidance = CFCollisionAvoidance(charging_cf, cf_args[charging_cf_uri][0][1])
                    charging_cf_avoidance.start_avoid(status_list)
        except KeyboardInterrupt:
            print('ctrl+c incoming')
            current_formation_number = 0
            end_all = True


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    factory = CachedCfFactory(rw_cache='./cache')
    with PublicSWarm(uris, factory=factory) as swarm:
        # If the copters are started in their correct positions this is
        # probably not needed. The Kalman filter will have time to converge
        # any way since it takes a while to start them all up and connect. We
        # keep the code here to illustrate how to do it.
        swarm.parallel(reset_estimator)

        # The current values of all parameters are downloaded as a part of the
        # connections sequence. Since we have 10 copters this is clogging up
        # communication and we have to wait for it to finish before we start
        # flying.
        print('Waiting for parameters to be downloaded...')
        swarm.parallel(wait_for_param_download)

        scfs = swarm.get_all_scfs()

        swarm.parallel_unblock(run_sequence, args_dict=cf_args)
        #global_dispatch()
