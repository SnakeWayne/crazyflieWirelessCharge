import time
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

class FlyPosture(Enum):
    flying=1
    hover=2
    changing=3
    charging=4
 
 
class CFSequence:
    sequence=[x,y,z,time]
    url='radio://0/40/2M/E7E7E7E7E7'
    current_sequence = i
    
    
    @staticmethod
    def getSequence():
        return sequence
     
    @staticmethod
    def setSequence(i=[]):
        sequence=i
        
    
        
    @staticmethod
    def getCurrentSequence():
        return current_sequence
     
class CFStatus:
     url='radio://0/40/2M/E7E7E7E7E7'
     current_position=[x,y,z]
     current_battery=电量
     current_posture=FlyPosture   #(刻画当前状态)
     
     
     @staticmethod
     def getCurrentPosition():
     
         if current_posture = 1
         return -1
         
         else
         return current_position
         
     @staticmethod
     def getCurrentBattery():
         return current_battery
         
         
     @staticmethod
     def getCurrentPosture():
         return current_posture
         
     @staticmethod
     def setCurrentPosition(i=[]):
         current_Position=i
         
     @staticmethod 
     def setCurrentBattery(i):
         current_battery=i
