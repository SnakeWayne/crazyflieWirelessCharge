# -*- coding: utf-8 -*-

from threading import Thread

from cflib.crazyflie.swarm import Swarm


class PublicSWarm(Swarm):
    def get_all_scfs(self):
        """
        Return the list of all the scfs, you can get the scf by uri

        :return: list of all the scfs
        """
        return self._cfs

    def parallel_unblock(self, func, args_dict=None):
        """
        Execute a function for all Crazyflies in the swarm, in parallel.
        One thread per Crazyflie is started to execute the function. The
        threads are joined at the end. Exceptions raised by the threads are
        ignored.

        just delete the thread.join() from the original one to let the main thread continue

        For a description of the arguments, see sequential()

        :param func:
        :param args_dict:
        """
        try:
            self.parallel_safe_unblock(func, args_dict)
        except Exception:
            pass

    def parallel_safe_unblock(self, func, args_dict=None):
        """
        Execute a function for all Crazyflies in the swarm, in parallel.
        One thread per Crazyflie is started to execute the function. The
        threads are joined at the end and if one or more of the threads raised
        an exception this function will also raise an exception.

        just delete the thread.join() from the original one to let the main thread continue

        For a description of the arguments, see sequential()

        :param func:
        :param args_dict:
        """
        threads = []
        reporter = self.Reporter()

        for uri, scf in self._cfs.items():
            args = [func, reporter] + \
                   self._process_args_dict(scf, uri, args_dict)

            thread = Thread(target=self._thread_function_wrapper, args=args)
            threads.append(thread)
            thread.start()

        if reporter.is_error_reported():
            raise Exception('One or more threads raised an exception when '
                            'executing parallel task')
