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

        _min_battery = 100
        _max_battery = 0
        _flying_patch = 0  # 飞行中需要交换的无人机
        _charging_patch = 1  # 充电中需要交换的无人机
        _safe_battery = 20  # 安全电量

        # 找出飞行中电量最低的无人机
        for i in list_flying:
            if list_flying[i].current_battery < _min_battery:
                _flying_patch = i
                _min_battery = list_flying[i].current_battery

        # 找出充电中电量最高的无人机
        for i in list_charging:
            if list_charging[i].current_battery > _max_battery:
                _charging_patch = i
                _max_battery = list_charging[i].current_battery

        # 虽说初始状态不一定，但这样设置能满足初始电量一样或电量差比较多的情况，不仅有一个底线，还有电量都比较多情况下的梯度变化
        _patch_min_battery = 80 - n * 20  # 需要调度的最低变量
        _n = _n + 1
        if _patch_min_battery < _safe_battery:
            _patch_min_battery = _safe_battery

        # 判断一下是否需要调度
        if _min_battery < _patch_min_battery:
            return list_flying[_flying_patch].url, list_charging[_charging_patch].url
        elif len(list_charging) == 0:
            return "abort", "abort"
        elif _max_battery < _safe_battery:
            return "abort", "abort"
        else:
            return "radio", "radio"




'''

    def position_callback(timestamp, data, logconf):
        print(data)

    @staticmethod
    def add_callback_to_singlecf(status_list):
        if __name__ == '__main__':
            cflib.crtp.init_drivers(enable_debug_driver=False)
            log_conf = LogConfig(name='Position', period_in_ms=500)
            log_conf1 = LogConfig(name='Battery', period_in_ms=500)
            #对要获取到的参数进行log注册
            log_conf.add_variable('ranging.distance2', 'float')
            log_conf1.add_variable('battery', 'float')

        #对list中的每个无人机状态进行更新
        for i in list:
            with SyncCrazyflie(list[i].url, cf=Crazyflie(rw_cache='./cache')) as scf:
                #位置信息
                scf.cf.log.add_config(log_conf)
                log_conf.data_received_cb.add_callback(position_callback)

                #电量信息
                scf.cf.log.add_config(log_conf1)
                log_conf1.data_received_cb.add_callback(position_callback)


'''