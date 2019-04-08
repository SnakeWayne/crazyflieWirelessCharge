# -*- coding: utf-8 -*-
"""
这个类负责无人机的调度轮换，通过传入无人机的URI和Status list对充电无人机和飞行的无人机进行轮换调度。

"""

import time
import math
from cflib import crazyflie
import cflib.crtp
from src import swarmFly


class FlyControl():

    @staticmethod
    def switch_to_charge(formation_cf_uri,charging_cf_uri,status_list):
        #获取两个uri的scf

        charging_cf_position = []  #充电的无人机位置
        static_charging_cf_position = []
        formation_cf_position = []  #编队中的无人机位置
        static_formation_cf_position = []
        min_x_distance = 0.15  #当前无人机和队列中其他x轴上的最小距离
        min_y_distance = 0.15
        min_z_distance = 0.15
        min_xy_distance = math.sqrt(min_x_distance * min_y_distance)    #当前无人机和队伍中其他无人机在xy平面上的最小距离
        current_z_distance = 0
        current_xy_distance = 0


        #根据uri获取充电的无人机的位置
        for sts in status_list:
            global static_charging_cf_position
            if charging_cf_uri==sts.uri:
                charging_cf_position = sts.current_position #建立引用
                static_charging_cf_position = list(sts.current_position)

        #根据uri获取编队中无人机位置
        for sts in status_list:
            global static_formation_cf_position
            if formation_cf_uri==sts.uri:
                formation_cf_position = sts.current_position
                static_formation_cf_position = list(sts.current_position)

        charging_cf = crazyflie.Crazyflie()
        formation_cf = crazyflie.Crazyflie()

        while current_xy_distance < min_xy_distance:
            #记录当前飞机和队列中任意一架飞机在xy平面方向的距离
            #扫描所有x负半轴方向的飞机，如果x轴的距离太近，判断y轴方向的距离
            for i in range(len(status_list)):
                if(formation_cf_uri == status_list[i].uri):
                    pass
                elif (status_list[i].current_position[0] - formation_cf_position[0] >0 and
                        status_list[i].current_position[0] - formation_cf_position[0] <min_x_distance):
                    if (status_list[i].current_position[1] - formation_cf_position[1] >0 and
                        status_list[i].current_position[1] - formation_cf_position[1] < min_y_distance):
                        #y轴正方向min_y_distance距离内有无人机，要向负方向飞行一段,实际场景中无人机不能靠的太近
                    elif (formation_cf_position[1] - status_list[i].current_position[1] > 0 and
                        formation_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
                        #y轴负方向上有无人机且距离过近，要向y正方向飞行一段
                elif (formation_cf_position[0] - status_list[i].current_position[0] > 0 and
                     formation_cf_position[0] - status_list[i].current_position[0] < min_x_distance):
                    if (status_list[i].current_position[1] - formation_cf_position[1]>0 and
                         status_list[i].current_position[1] - formation_cf_position[1] < min_y_distance):
                        #飞控
                    elif  (formation_cf_position[1] - status_list[i].current_position[1] > 0 and
                        formation_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
                        #飞控

            #xy方向调整完毕
            #计算所有无人机和当前无人机之间的最短距离
            current_xy_distance = 999999    #重新赋值一个大数方便判断
            for i in range(len(status_list)):
                if(formation_cf_uri != status_list[i].uri):
                    temp = math.sqrt(abs((formation_cf_position[0]-status_list[i].current_position[0])*\
                                 formation_cf_position[1]-status_list[i].current_position[1]))
                if(temp < current_xy_distance):
                    current_xy_distance = temp

        #调整z轴
        while current_z_distance < min_z_distance:
             for i in range(len(status_list)):
                 if (abs(formation_cf_position[2]-status_list[i].current_position[2])<min_z_distance and
                     formation_cf_uri != status_list[i].uri):
                    #向下飞

             current_z_distance = 999999
             for i in range(len(status_list)):
                 if status_list[i].uri != formation_cf_uri:
                    temp = abs(formation_cf_position[2]-status_list[i].current_position[2])
                 if temp < current_z_distance
                     current_z_distance = temp
        #z轴调整完毕
        #在这里悬停，等待charging_cf的调整。先从xy方向飞到充电板正上方，再降落

        #charing_cf起飞并向某个方向飞行20cm为formation_cf留出降落的位置，悬停，改变状态为changing
        for i in range(len(status_list)):
            if(charging_cf_uri==status_list[i].uri):
                status_list[i].current_posture = FlyPosture.changing

        #扫描Z轴上有没有合适的空间
        current_z_distance = 0
        while current_z_distance < min_z_distance:
            for i in range(len(status_list)):
                if(status_list[i].uri != charging_cf_uri and
                    abs(charging_cf_position[2] - status_list[i].current_position[2]) < min_z_distance):
                    #向上飞直到没有飞机和它处于同一个平面

        #飞到原来队伍中的飞机的xy位置

        #判断min_xy_distance,飞到原来队伍中的飞机的z的高度，再回到xy位置
        while current_xy_distance < min_xy_distance:
            #记录当前飞机和队列中任意一架飞机在xy平面方向的距离
            #扫描所有x负半轴方向的飞机，如果x轴的距离太近，判断y轴方向的距离
            for i in range(len(status_list)):
                if(formation_cf_uri == status_list[i].uri):
                    pass
                elif (status_list[i].current_position[0] - formation_cf_position[0] >0 and
                        status_list[i].current_position[0] - formation_cf_position[0] <min_x_distance):
                    if (status_list[i].current_position[1] - formation_cf_position[1] >0 and
                        status_list[i].current_position[1] - formation_cf_position[1] < min_y_distance):
                        #y轴正方向min_y_distance距离内有无人机，要向负方向飞行一段,实际场景中无人机不能靠的太近
                    elif (formation_cf_position[1] - status_list[i].current_position[1] > 0 and
                        formation_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
                        #y轴负方向上有无人机且距离过近，要向y正方向飞行一段
                elif (formation_cf_position[0] - status_list[i].current_position[0] > 0 and
                     formation_cf_position[0] - status_list[i].current_position[0] < min_x_distance):
                    if (status_list[i].current_position[1] - formation_cf_position[1]>0 and
                         status_list[i].current_position[1] - formation_cf_position[1] < min_y_distance):
                        #飞控
                    elif  (formation_cf_position[1] - status_list[i].current_position[1] > 0 and
                        formation_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
                        #飞控



        #传递sequence














