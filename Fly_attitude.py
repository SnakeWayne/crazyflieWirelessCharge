import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

class FlyPosture(Enum):
    flying=1 #正在飞行中
    hover=2  #等待队列调整
    changing=3 #被选中无人机正在进行调度
    charging=4 #正在充电
 
 
class CFSequence:
    sequence=[x,y,z,time]
    url='radio://0/40/2M/E7E7E7E7E7'
    current_sequence = i
    
    
    def getSequence():
        return sequence
     
    def setSequence(i=[]):
        sequence=i
        
    def getCurrentSequence():
        return current_sequence
     
class CFStatus:
     url='radio://0/40/2M/E7E7E7E7E7'
     current_position=[x, y, z]  #不再单独存储无线充电座位置，如果发现posture是充电中，则就认为此position为充电座position
     current_battery=电量
     current_posture=FlyPosture   #(刻画当前状态)
     
     

     def getCurrentPosition():
        if current_posture == 1
            return -1
         
         else
            return current_position
         
  
     def getCurrentBattery():
         return current_battery
         
         
     def getCurrentPosture():
         return current_posture
         
     
     def setCurrentPosition(i=[]):
         current_Position=i
         
     
     def setCurrentBattery(i):
         current_battery=i
