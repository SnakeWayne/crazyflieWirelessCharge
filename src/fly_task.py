# -*- coding: utf-8 -*-

import threading
import time
import math
import numpy
import operator
from fly_attr import FlyPosture
from fly_attr import CFStatus
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander


# 飞行任务类
class CFFlyTask:
    _formation_number = 0  # 本次飞行任务无人机个数
    _sync_number = 0  # 用于判断是否所有无人机都正常完成当前任务
    _switch_pair_list = None  # 存储当前需要交换的无人机每个pair
    _sync_number_lock = threading.Lock()  # 多机同步时需要的锁

    def __init__(self, cf, status, trajectory_list, trajectory_index=0):
        """
        初始化参数
        :param cf:无人机
        :param status:用于保存一个status引用
        :param trajectory_list:每一项为飞行轨迹类对象
        :param trajectory_index:当前飞行轨迹的下标
        """
        self._cf = cf
        self._status = status
        self._trajectory_list = trajectory_list
        self._trajectory_index = trajectory_index
        self._status_lock = self._status.status_lock

    def set_cf_afterword(self, cf):
        self._cf = cf

    @staticmethod
    def set_switch_pair_list(switch_pair_list):
        CFFlyTask._switch_pair_list = switch_pair_list

    @staticmethod
    def set_formation_number(number):
        CFFlyTask._formation_number = number

    @staticmethod
    def not_close_enough(point1,point2):
        x1 = point1[0]
        y1 = point1[1]
        z1 = point1[2]
        x2 = point2[0]
        y2 = point2[1]
        z2 = point2[2]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) > 0.05

    def __getattr__(self, item):
        if item == 'trajectory_list':
            return self._trajectory_list
        elif item == 'trajectory_index':
            return self._trajectory_index
        else:
            print(item)
            raise AttributeError('没有这个属性')

    def copy(self, fly_task):
        self._trajectory_list = fly_task.trajectory_list
        self._trajectory_index = fly_task.trajectory_index

    def run(self):
        while self._trajectory_index < len(self._trajectory_list):
            if self._status.current_posture == FlyPosture.charging:
                return
            trajectory = self._trajectory_list[self._trajectory_index]
            if not trajectory.is_over():
                self.run_single_trajectory(trajectory)
            with CFFlyTask._sync_number_lock:  # 完成一段的飞行序列，进入悬停等待状态
                with self._status_lock:
                    self._status.current_posture = FlyPosture.hovering
                CFFlyTask._sync_number += 1
            while CFFlyTask._sync_number % CFFlyTask._formation_number != 0:  # 在悬停等待的时候可能发生避障或者无人机更换
                time.sleep(0.1)
                if self._status.current_posture == 'avoiding':
                    continue
                elif CFFlyTask._switch_pair_list['formation'][0] == self._cf.link_uri:
                    self.formation_fly_to_charge(
                        self._status.current_position, CFFlyTask._switch_pair_list['charging'][1])
                    with self._status_lock:
                        self._status.current_posture = FlyPosture.charging
                    break
            self._trajectory_index += 1
            with self._status_lock:
                self._status.current_posture = FlyPosture.flying
        commander = DuplicablePositionHlCommander(self._cf)  # 飞行完所有序列之后，停掉无人机，eventually_land会修改状态为over，用于将无人机线程停掉。
        commander.eventually_land()

    def formation_fly_to_charge(self, start, end):  # 相比run_single_trajectory不考虑调度情况，因为本身执行的就是调度任务，其余逻辑相同相同
        trajectory = CFTrajectoryFactory.line(start, end)
        commander = DuplicablePositionHlCommander(self._cf)
        commander.take_off()
        current_point = 0
        while True:
            point = trajectory.get_next_point()
            if point is not None:
                current_point = point
                self._status.current_end_point = trajectory.get_current_end_point()
                if self._status.current_posture == 'avoiding':
                    time.sleep(0.3)
                    continue
                else:
                    commander.go_to(current_point[0],current_point[1],current_point[2])
                    time.sleep(0.1)
            else:
                while CFFlyTask.not_close_enough(self._status, current_point):
                    if self._status.current_posture == 'avoiding':
                        time.sleep(0.1)
                        continue
                    else:
                        commander.go_to(current_point[0],current_point[1],current_point[2])
                        time.sleep(0.1)
                return

    def run_single_trajectory(self, trajectory):  # 运行单个trajectory
        if trajectory.posture == FlyPosture.hovering:
            return
        commander = DuplicablePositionHlCommander(self._cf)
        commander.take_off()
        current_point = 0
        while True:
            point = trajectory.get_next_point()
            if point is not None:
                current_point = point  # 不是最后一个点的话赋值
                self._status.current_end_point = trajectory.get_current_end_point()  # 更新当前终点
                if self._status.current_posture == 'avoiding':
                    time.sleep(0.3)  # 避障的时候更新点的速度减慢
                    continue
                elif CFFlyTask._switch_pair_list['formation'][0] == self._cf.link_uri:  # 是否为交换无人机
                    self.formation_fly_to_charge(
                        self._status.current_position, CFFlyTask._switch_pair_list['charging'][1])
                    with self._status_lock:
                        self._status.current_posture = FlyPosture.charging
                    return
                else:
                    commander.go_to(current_point[0],current_point[1],current_point[2])
                    time.sleep(0.1)
            else:
                while CFFlyTask.not_close_enough(self._status, current_point):  # 有可能避障完成之后已经便利到终点，但是偏离实际位置，所以还是要修正的，修正过程中也会有避障可能
                    if self._status.current_posture == 'avoiding':
                        time.sleep(0.1)
                        continue
                    elif CFFlyTask._switch_pair_list['formation'][0] == self._cf.link_uri:
                        self.formation_fly_to_charge(
                            self._status.current_position, CFFlyTask._switch_pair_list['charging'][1])
                        with self._status_lock:
                            self._status.current_posture = FlyPosture.charging
                        return
                    else:
                        commander.go_to(current_point[0],current_point[1],current_point[2])
                        time.sleep(0.1)
                return


# 飞行轨迹类
class CFTrajectory:

    def __init__(self, posture, point_list, current_point_index=0):
        """
        :param posture:描述本次飞行任务是飞行还是悬停
        :param point_list:由xyz组成的list 存储当前路径上一系列点
        :param current_point_index:存储当前点下标
        """
        self._posture = posture
        if posture == FlyPosture.hovering:
            pass
        else:
            self._point_list = point_list
            self._current_point_index = current_point_index
            self._end_point_index_list = self._calculate_end_points_index()

    def __getattr__(self, item):
        if item == 'posture':
            return self._posture
        elif item == 'point_list':
            return self._point_list
        else:
            print(item)
            raise AttributeError('没有这个属性')

    def is_over(self):
        if self._current_point_index == len(self._point_list):
            return True
        else:
            return False

    def get_next_point(self):
        next_point = self._point_list[self._current_point_index]
        if self._current_point_index == len(self._point_list):
            return None
        else:
            self._current_point_index += 1
            return next_point

    def get_current_end_point(self):
        for end_point_index in range(len(self._end_point_index_list)):
            if end_point_index >= self._current_point_index:
                return self._point_list[end_point_index]

    @staticmethod
    def _calculate_distance_power(start_point, end_point):
        x1 = start_point[0]
        y1 = start_point[1]
        z1 = start_point[2]
        x2 = end_point[0]
        y2 = end_point[1]
        z2 = end_point[2]
        return (x2-x1)**2+(y2-y1)**2+(z2-z1)**2

    def _calculate_end_points_index(self):  # 每次相对于当前起点递增距离，到max时选定终点加入list，并将此终点作为当前起点
        end_point_index_list = []
        current_start_point_index = 0
        current_max_distance = -1
        for point_index in range(len(self._point_list)):
            if point_index+1 == len(self._point_list):
                end_point_index_list.append(self._point_list[point_index])
            elif CFTrajectory._calculate_distance_power(self._point_list[current_start_point_index],
                                                        self._point_list[point_index]) > current_max_distance:
                current_max_distance = CFTrajectory.\
                    _calculate_distance_power(self._point_list[current_start_point_index], self._point_list[point_index])
            else:
                end_point_index_list.append(point_index-1)
                current_start_point_index = point_index-1
                current_max_distance = -1

        return end_point_index_list


class CFTrajectoryFactory:

    def __init__(self):
        pass

    @staticmethod
    def line(start, end):
        """
            这里认为start和end都是三维空间中的点（三元组）,返回一个点集
        """
        start_x = start[0]
        start_y = start[1]
        start_z = start[2]
        end_x = end[0]
        end_y = end[1]
        end_z = end[2]
        vector = [end_x - start_x, end_y - start_y, end_z - start_z]  # 方向向量
        vector_length = numpy.linalg.norm(vector)
        for i in range(len(vector)):
            vector[i] = vector[i] / vector_length
        point_list = [start]
        ratio = 0
        while True:
            x_step = vector[0] * 0.05 * ratio
            y_step = vector[1] * 0.05 * ratio
            z_step = vector[2] * 0.05 * ratio
            if math.sqrt(x_step**2+y_step**2+z_step**2) > vector_length:
                break
            point_list.append([start_x+x_step, start_y+y_step, start_z+z_step])
            ratio += 1
        trajectory = CFTrajectory(FlyPosture.flying, point_list)
        return trajectory

    @staticmethod
    def arch(start, end, normal_vector):
        point_list = []
        start = numpy.array(start)
        end = numpy.array(end)
        normal_vec = numpy.array(normal_vector)
        middle = (start + end) / 2
        if numpy.inner(normal_vec, middle) != 0:
            print('法向量与直径不垂直，无法创建弧线')
            return None
        vec1 = start - middle
        rad = numpy.linalg.norm(vec1)
        vec2 = numpy.cross(vec1, normal_vec)
        vec1 = vec1 / numpy.linalg.norm(vec1)
        vec2 = vec2 / numpy.linalg.norm(vec2)
        step_length = 0.05 / rad

        for it_pi in numpy.arange(0, math.pi+step_length, step_length):  # 参照官方画圆的路径
            x = middle[0] + rad * (vec1[0] * math.cos(it_pi) + vec2[0] * math.sin(it_pi))
            y = middle[1] + rad * (vec1[1] * math.cos(it_pi) + vec2[1] * math.sin(it_pi))
            z = middle[2] + rad * (vec1[2] * math.cos(it_pi) + vec2[2] * math.sin(it_pi))
            point_list.append([x, y, z])
        trajectory = CFTrajectory(FlyPosture.flying, point_list)
        return trajectory

    @staticmethod
    def add(first, second):  # 将两个路径连接成一段路径
        point_list = []
        if operator.eq(first.point_list[-1], second.point_list[0]):
            for point_index in range(len(first.point_list)):
                point_list.append(first.point_list[point_index])
            for point_index in range(len(second.point_list)):
                if point_index == 0:
                    continue
                point_list.append(second.point_list[point_index])
            trajectory = CFTrajectory(FlyPosture.flying, point_list)
            return trajectory
        else:
            print('两段不连续无法相加')
            return None
