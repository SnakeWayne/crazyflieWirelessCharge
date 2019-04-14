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

from cf_dispatch import CFDispatch
from customcflib.public_swarm import PublicSWarm
from fly_attr import FlyPosture
from fly_control import FlyControl
from fly_attr import CFSequence
from fly_attr import CFStatus
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander

# is any cf dispatching
dispatching = False

# counter of how many cfs are hovering
hover_check = 0
hover_check_lock = threading.Lock()
fromation_number_lock = threading.Lock()

# counter of how many cf are still in formation
current_formation_number = 1  # temp

# Change uris and sequences according to your setup
URI1 = 'radio://0/10/2M/E7E7E7E7E7'
URI2 = 'radio://0/20/2M/E7E7E7E7E7'
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
sequence_list = [sequence1,sequence2]  # temp

# CFStatus, in the final version we may use a list to store it
status1 = CFStatus(URI1, FlyPosture.flying)  # temp
status2 = CFStatus(URI2, FlyPosture.flying)  # temp
status3 = CFStatus(URI3, FlyPosture.charging)  # temp

status_list = [status1,status2,status3]  # temp
DuplicablePositionHlCommander.set_class_status_list(status_list)

# used to pass param to the parallel thread
cf_args = {
    URI1: [[sequence1, status1]],
    URI2: [[sequence2, status2]],
    URI3: [[sequence2, status3]],
    }

# List of URIs, comment the one you do not want to fly
uris = {
    URI1,
    URI2,
    URI3
}

# Dict of scfs
scfs = []


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


def run_sequence(scf, cf_arg):
    """
    Task for one cf
    :param scf: the scf which do the task
    :param cf_arg: the dic value list, at [0] is obj CFSequence, at [1] is obj CFStatus
    :return: None
    """
    try:
        cf = scf.cf
        cf.param.set_value('flightmode.posSet', '1')
        CFDispatch.add_callback_to_singlecf(cf.link_uri, scf, cf_arg)
        global dispatching
        global hover_check
        global current_formation_number
        global status_list
        global sequence_list
        global end_all
        with DuplicablePositionHlCommander(scf) as commander:
            print('before run sequnce',status_list)
            for sta in status_list:
                print(sta.current_position)
            while True:
                if end_all:
                    break
                else:
                    if dispatching:  # judge if there is two cf switching to charge
                        if cf_arg[1].current_posture == FlyPosture.flying:
                            cf_arg[1].current_posture = FlyPosture.hovering
                            with hover_check_lock:
                                hover_check += 1
                            while True:
                                if dispatching:
                                    time.sleep(0.1)
                                else:
                                    cf_arg[1].current_posture = FlyPosture.flying
                                    break
                        elif cf_arg[1].current_posture == FlyPosture.charging:
                            while True:
                                if dispatching:
                                    time.sleep(1)
                                else:
                                    break
                    else:
                        if cf_arg[1].current_posture == FlyPosture.flying:  # if not dispatching and you are flying just fly
                            commander.take_off()
                            position = cf_arg[0].next
                            if position == None:
                                with formation_number_lock:
                                    current_formation_number -= 1
                                commander.land()
                                status_list.remove(cf_arg[1])
                                break
                            print(cf.link_uri,'is flying')
                            print('Setting position {}'.format(position))
                            end_time = time.time() + position[3]
                            commander.go_to(position[0],position[1],position[2])
                            time.sleep(position[3])
                        elif cf_arg[1].current_posture == FlyPosture.charging:
                            time.sleep(0.1)
                            if current_formation_number == 0:
                                break
    except Exception as e:
        print(e)

def global_dispatch():
    global cf_args
    global dispatching
    global hover_check
    global current_formation_number
    global status_list
    global sequence_list
    global scfs
    global end_all
    while True:
        try:
            time.sleep(10)
            if current_formation_number == 0:
                break
            formation_cf_uri, charging_cf_uri = CFDispatch.calculate_how_to_dispatch(status_list)

            if formation_cf_uri == 'radio':  # temp define invalid uri
                continue
            elif formation_cf_uri == 'abort':
                print('we should land')  # flycontrol need
                # tell every one to land, maybe set the current sequence to max for all
            else:
                print('switching')
                dispatching = True
                while hover_check < current_formation_number:  # wait for all flying cfs to hover
                    time.sleep(1)
                print('all plane have already in hover mode')
                formation_cf =  scfs[formation_cf_uri].cf
                charging_cf = scfs[charging_cf_uri].cf
                FlyControl.switch_to_charge(formation_cf, charging_cf, status_list)
                #print('determine which two to switch')
                sequence = cf_args[formation_cf_uri][0][0]

                # update the sequence and posture
                cf_args[charging_cf_uri][0][0] = sequence
                cf_args[formation_cf_uri][0][1].current_posture = FlyPosture.charging
                cf_args[charging_cf_uri][0][1].current_posture = FlyPosture.flying
                with hover_check_lock:
                    hover_check = 0
                dispatching = False
        except KeyboardInterrupt:
            print('ctrl+c incoming')
            current_formation_number = 0
            end_all = True
            dispatching = False



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
        global_dispatch()
