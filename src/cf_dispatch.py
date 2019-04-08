# -*- coding: utf-8 -*-

import cflib.crtp

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger


class CFDispatch():

    _n = 0  # 用于判断当前调度情况

    @staticmethod
    def calculate_how_to_dispatch(status_list):

        list_flying = []  # 飞行中的无人机
        list_charging = []  # 充电中的无人机

        # 遍历list根据状态分为飞行中和充电中
        for i in list:
            if status_list[i].current_posture == FlyPosture.flying:
                list_flying.append(status_list[i])
            elif status_list[i].current_posture == FlyPosture.charging:
                list_charging.append(status_list[i])

        min_battery = 100
        max_battery = 0
        flying_patch = 0  # 飞行中需要交换的无人机
        charging_patch = 1  # 充电中需要交换的无人机
        safe_battery = 20  # 安全电量

        # 找出飞行中电量最低的无人机
        for i in list_flying:
            if list_flying[i].current_battery < min_battery:
                flying_patch = i
                min_battery = list_flying[i].current_battery

        # 找出充电中电量最高的无人机
        for i in list_charging:
            if list_charging[i].current_battery > max_battery:
                charging_patch = i
                max_battery = list_charging[i].current_battery

        # 虽说初始状态不一定，但这样设置能满足初始电量一样或电量差比较多的情况，不仅有一个底线，还有电量都比较多情况下的梯度变化
        patch_min_battery = 80 - CFDispatch._n * 20  # 需要调度的最低变量
        CFDispatch._n = CFDispatch._n + 1
        if patch_min_battery < safe_battery:
            patch_min_battery = safe_battery

        # 判断一下是否需要调度
        if min_battery < patch_min_battery:
            return list_flying[flying_patch].url, list_charging[charging_patch].url
        elif max_battery < safe_battery:
            return "abort", "abort"
        else:
            return "radio", "radio"

    @staticmethod
    def update_cfstatus(timestamp, data, logconf, cf_args, uri):
        status = cf_args[uri][1]
        status.current_position = [data['kalman.stateX'], data['kalman.stateY'], data['kalman.stateZ']]
        status.current_battery = data['pm.vbat'] * 10

    @staticmethod
    def add_callback_to_singlecf(uri, scf, cf_args):
        cflib.crtp.init_drivers(enable_debug_driver=False)
        log_conf = LogConfig(name=uri, period_in_ms=500)
        log_conf.add_variable('kalman.stateX', 'float')
        log_conf.add_variable('kalman.stateY', 'float')
        log_conf.add_variable('kalman.stateZ', 'float')
        log_conf.add_variable('pm.vbat', 'float')
        scf.cf.log.add_config(log_conf)

        def outer_callback(timestamp, data, logconf):
            return CFDispatch.update_cfstatus(timestamp, data, logconf, cf_args, uri)
        log_conf.data_received_cb.add_callback(outer_callback)
        log_conf.start()

