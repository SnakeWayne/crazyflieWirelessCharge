# -*- coding: utf-8 -*-

import cflib.crtp

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from fly_attr import FlyPosture
import math

ax = plt.axes(projection='3d')
#plt.close()  # clf() # 清图  cla() # 清坐标轴 close() # 关窗口
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_xlim(-3,3)
ax.set_ylim(-3,3)
ax.set_zlim(-1,4)
color_dic = {'radio://0/20/2M/E7E7E7E7E7': '#00CED1', 'radio://0/00/2M/E7E7E7E7E7': '#DC143C'}
area = math.pi * 4 ** 2
plt.grid(True)  # 添加网格
ax.scatter(0,0,0, c=color_dic['radio://0/20/2M/E7E7E7E7E7'], alpha=0.4, label='radio://0/20/2M/E7E7E7E7E7')  # 散点图
plt.pause(5)
      
