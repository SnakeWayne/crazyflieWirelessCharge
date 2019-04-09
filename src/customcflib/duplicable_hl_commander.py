# -*- coding: utf-8 -*-
import math
import time

from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander


class DuplicablePositionHlCommander(PositionHlCommander):
    """The position High Level Commander, which support multiple commander with the same scf
    by passing a constantly changing status_list obj, its possess by the class and each obj own a status"""

    CONTROLLER_PID = 1
    CONTROLLER_MELLINGER = 2

    DEFAULT = None

    def __init__(self, crazyflie,
                 x=0.0, y=0.0, z=0.0,
                 default_velocity=0.5,
                 default_height=0.5,
                 controller=CONTROLLER_PID):
        """
        Construct an instance of a PositionHlCommander

        :param crazyflie: a Crazyflie or SyncCrazyflie instance
        :param x: Initial position, x
        :param y: Initial position, y
        :param z: Initial position, z
        :param default_velocity: the default velocity to use
        :param default_height: the default height to fly at
        :param controller: Which underlying controller to use
        """
        if isinstance(crazyflie, SyncCrazyflie):
            self._cf = crazyflie.cf
        else:
            self._cf = crazyflie

        self._default_velocity = default_velocity
        self._default_height = default_height
        self._controller = controller

        self.__status = self._get_status(self._cf)

        self._x = self.__status.current_position[0]
        self._y = self.__status.current_position[1]
        self._z = self.__status.current_position[2]
        self._is_flying = False

    @staticmethod
    def set_class_status_list(status_list):
        """
        always call this func before you initialize any obj
        :param status_list: the constantly changing status_list obj
        :return:
        """
        DuplicablePositionHlCommander._status_list = status_list

    def _get_status(self, cf):
        for i in range(len(DuplicablePositionHlCommander._status_list)):
            if DuplicablePositionHlCommander._status_list[i].uri == cf.link_uri:
                return DuplicablePositionHlCommander._status_list[i]

    def land(self, velocity=DEFAULT):
        """
        Go straight down and turn off the motors.

        Do not call this function if you use the with keyword. Landing is
        done automatically when the context goes out of scope.

        :param velocity: The velocity (meters/second) when going down
        :return:
        """
        if self._is_flying:
            duration_s = self.__status.current_position[2] / self._velocity(velocity)
            self._hl_commander.land(0, duration_s)
            time.sleep(duration_s)
            self._z = 0.0

            self._hl_commander.stop()
            self._is_flying = False

    def move_distance(self, distance_x_m, distance_y_m, distance_z_m,
                      velocity=DEFAULT):
        """
        Move in a straight line.
        positive X is forward
        positive Y is left
        positive Z is up

        :param distance_x_m: The distance to travel along the X-axis (meters)
        :param distance_y_m: The distance to travel along the Y-axis (meters)
        :param distance_z_m: The distance to travel along the Z-axis (meters)
        :param velocity: the velocity of the motion (meters/second)
        :return:
        """

        x = self.__status.current_position[0] + distance_x_m
        y = self.__status.current_position[1] + distance_y_m
        z = self.__status.current_position[2] + distance_z_m

        self.go_to(x, y, z, velocity)

    def go_to(self, x, y, z=DEFAULT, velocity=DEFAULT):
        """
        Go to a position

        :param x: X coordinate
        :param y: Y coordinate
        :param z: Z coordinate
        :param velocity: the velocity (meters/second)
        :return:
        """

        z = self._height(z)

        dx = x - self.__status.current_position[0]
        dy = y - self.__status.current_position[1]
        dz = z - self.__status.current_position[2]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        duration_s = distance / self._velocity(velocity)
        self._hl_commander.go_to(x, y, z, 0, duration_s)
        time.sleep(duration_s)

        self._x = x
        self._y = y
        self._z = z

    def get_position(self):
        """
        Get the current position
        :return: (x, y, z)
        """
        return self.__status.current_position[0], self.__status.current_position[1], self.__status.current_position[2]

    def _reset_position_estimator(self):
        self._cf.param.set_value('kalman.initialX', '{:.2f}'.format(self.__status.current_position[0]))
        self._cf.param.set_value('kalman.initialY', '{:.2f}'.format(self.__status.current_position[1]))
        self._cf.param.set_value('kalman.initialZ', '{:.2f}'.format(self.__status.current_position[2]))

        self._cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        self._cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)
