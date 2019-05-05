# -*- coding: utf-8 -*-
from enum import Enum


class FlyPosture(Enum):

    flying = 1  # 正在飞行中

    hovering = 2   # 等待队列调整

    changing = 3  # 被选中无人机正在进行调度

    charging = 4  # 正在充电

    avoiding = 5  # 正在避障

    over = 6  # 完成全部飞行任务


class CFSequence:

    def __init__(self, sequence, current_sequence_index=0):
        """
        初始化参数，不允许中途修改
        :param sequence: 飞行任务队列四元组list，飞行具体位置xyz，飞行悬停时间s
        :param uri: 无人机uri
        :param current_sequence_index: 当前飞行任务序列下标
        """
        self._sequence = sequence
        self._current_sequence_index = current_sequence_index

    def __getattr__(self, item):
        if item == 'sequence':
            return self._sequence
        elif item == 'current_sequence_index':
            return self._current_sequence_index
        elif item == 'current_sequence':
            return self._sequence[self._current_sequence_index]
        elif item == 'next':  # 仿写java iterable的风格
            self._current_sequence_index += 1
            if self._current_sequence_index <= len(self._sequence):
                return self._sequence[self.current_sequence_index - 1]
            else:
                return None
        else:
            print(item)
            raise AttributeError('没有这个属性')


class CFStatus:
    def __init__(self, uri, current_posture, status_lock, current_position=None, current_battery=100, current_end_point=None):
        """
        初始化时瞎赋值，只要求uri,current_posture,status_lock必须提供就行了
        :param uri: 无人机地址
        :param current_posture: FlyPosture所定义的几种姿态
        :param status_lock: 多线程修改current_posture时所需要的锁
        :param current_position: xyz三元组
        :param current_battery: 100为满电，0为无电
        :param current_end_point: 当前终点，避障用
        """
        self._uri = uri
        if current_position == None:
            self._current_position = [0, 0, 0]
        else:
            self._current_position = current_position
        self._current_battery = current_battery
        self._status_lock = status_lock
        self._current_posture = current_posture
        self._current_end_point = current_end_point

    def __getattr__(self, item):
        if item == 'uri':
            return self._uri
        elif item == 'current_position':
            return self._current_position
        elif item == 'current_battery':
            return self._current_battery
        elif item == 'current_posture':
            return self._current_posture
        elif item == 'current_end_point':
            return self._current_end_point
        elif item == 'status_lock':
            return self._status_lock
        else:
            raise AttributeError('没有这个属性')

    def __setattr__(self, key, value):
        if key == 'uri':
            super().__setattr__('_uri', value)
        elif key == 'current_position':
            super().__setattr__('_current_position', value)
        elif key == 'current_battery':
            super().__setattr__('_current_battery', value)
        elif key == 'current_posture':
            super().__setattr__('_current_posture', value)
        elif key == 'current_end_point':
            super().__setattr__('_current_end_point', value)
        elif key == 'current_posture':
            super().__setattr__('_current_posture', value)
        else:
            super().__setattr__(key, value)



