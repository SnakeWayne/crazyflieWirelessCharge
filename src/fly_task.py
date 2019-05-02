# -*- coding: utf-8 -*-

import threading
import time
from fly_attr import FlyPosture
from fly_attr import CFStatus


# 飞行任务类
class CFFlyTask:
    _formation_number = 0  # 本次飞行任务无人机个数
    _sync_number = 0  # 用于判断是否所有无人机都正常完成当前任务
    switch_pair_list = None  # 存储当前需要交换的无人机每个pair

    def __init__(self, cf, status, trajectory_list, trajectory_index=0):
        """
        初始化参数
        :param cf:无人机
        :param status:用于保存一个status引用
        :param trajectory_list:每一项为飞行轨迹类对象
        :param trajectory_index:当前飞行轨迹的下标
        :param status_lock:
        """
        self._cf = cf
        self._status = status
        self._trajectory_list = trajectory_list
        self._trajectory_index = trajectory_index
        self._status_lock = threading.Lock()

    def run(self):
        for trajectory in self._trajectory_list:
            self.run_single_trajectory(trajectory)
        if self._formation_number == self._sync_number:
            return

    def run_single_trajectory(self, point_list):
        for point in CFTrajectory.get_next_point(point_list):
            if self._status._current_posture == 'avoiding':
                pass
            elif self._status._current_posture == 'hovering':
                self._status_lock.acquire()
                try:
                    self._sync_number += 1
                finally:
                    self._status_lock.release()
                time.sleep(1.0)     # 这里我不知道要sleep多久
            else:
                for dict in switch_pair_list:
                    if self.cf == dict['formation'[0]]:
                        fomation_charge_switch(dict['formation'[1]],dict['charging'[1]])
                        self._status_lock.acquire()
                        try:
                            self._status._current_posture == 'changing'
                        finally:
                            self._status_lock.release()
                    elif CFTrajectory.get_next_point(self._trajectory_list) is None:
                        self._status_lock.acquire()
                        try:
                            self._status._current_posture == 'hovering'
                            self._sync_number += 1
                        finally:
                            self._status_lock.release()
                    else:
                        commander.go_to(CFTrajectory.get_next_point(self._trajectory_list))

    @staticmethod
    def formation_charge_switch(start, end):
        point_list = CFTrajectoryFactory.line(start, end)
        trajectory = CFTrajectory(changing, point_list, current_point_index=0)
        return trajectory


# 飞行轨迹类
class CFTrajectory:

    def __init__(self, posture, point_list, current_point_index=0):
        """

        :param posture:描述本次飞行任务是飞行还是悬停
        :param point_list:由xyz组成的list 存储当前路径上一系列点
        :param current_point_index:存储当前点下标
        :param end_points_index_list:存储多个终点下标
        """
        self.posture = posture
        if posture == FlyPosture.hovering:
            pass
        else:
            self._point_list = point_list
            self._current_point_index = current_point_index
            self._end_point_index_list = self._calculate_end_points_index()

    def get_next_point(self):
        next_point = self._point_list[self._current_point_index]
        if self._point_list[self._current_point_index + 1] is None:
            pass
        else:
            self._current_point_index += 1
        return next_point

    def get_current_end_point(self):
        for index in len(self._end_point_index_list):
            if self._end_point_index_list[index] > self._current_point_index:
                return self._point_list[self._end_point_index_list[index]]

    @staticmethod
    def _calculate_distance(point):
        x = point[0]
        y = point[1]
        z = point[2]
        return x*x+y*y+z*z

    def _calculate_end_points_index(self):
        end_point_index_list = []
        for point in len(self._point_list):
            if self._point_list[point + 1] is None:
                end_point_index_list.append(self._point_list[point])
            elif _calculate_distance(self._point_list[point]) > _calculate_distance(self._point_list[point+1]):
                end_point_index_list.append(self._point_list[point])
        return end_point_index_list


class CFTrajectoryFactory:

    def __init__(self):
        pass

    @staticmethod
    def line(start, end):
        """
            这里认为start和end都是三维空间中的点（三元组）,返回一个点集
        """
        startx = start[0]
        starty = start[1]
        startz = start[2]
        endx = end[0]
        endy = end[1]
        endz = end[2]
        vector = [endx - startx, endy - starty, endz - startz]  # 方向向量
        maxnum = max(vector)
        for axis in len(vector):
            vector[axis] = vector[axis] / maxnum
        point_list = [start]
        newx = startx
        newy = starty
        newz = startz
        while (newx + vector[0] * 0.05) <= endx:
            newx += vector[0] * 0.05
            newy += vector[1] * 0.05
            newz += vector[2] * 0.05
            point_list.append(newpoint[newx, newy, newz])
        trajectory = CFTrajectory(flying, point_list, 0)
        return trajectory

    @staticmethod
    def arch(start, end, normal_vector):
        pass
        # 圆弧这部分我暂时没想出来怎么比较好地实现...

    @staticmethod
    def add(first, second):
        for point in len(second):
            first.append(second[point])
        trajectory = CFTrajectory(flying, first, 0)
        return trajectory
