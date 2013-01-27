from time import sleep

import os
import sys
import thread


mtimes = {}


class Reloader(object):
    mtimes = {}

    @classmethod
    def code_changed(cls):
        for d, dirs, files in os.walk(sys.path[0]):
            for f in files:
                path = os.path.join(d, f)
                if path.endswith('.py'):
                    stat = os.stat(path)
                    if path in cls.mtimes and stat.st_mtime != cls.mtimes[path]:
                        cls.parent.logger.info('* Code change detected in %s, restarting...' % path.replace(sys.path[0] + '/', ''))
                        return True
                    cls.mtimes[path] = stat.st_mtime

    @classmethod
    def restart_with_reloader(cls):
        while True:
            args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions] + sys.argv
            new_environ = os.environ.copy()
            new_environ['MAIN_THREAD'] = 'true'
            exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
            if exit_code != 3:
                return exit_code

    @classmethod
    def run_with_reloader(cls, parent, func):
        cls.parent = parent
        if os.environ.get('MAIN_THREAD') == 'true':
            thread.start_new_thread(func, ())
            while True:
                if cls.code_changed():
                    sys.exit(3)
                sleep(1)
        else:
            try:
                exit_code = cls.restart_with_reloader()
                if exit_code < 0:
                    os.kill(os.getpid(), -exit_code)
                else:
                    sys.exit(exit_code)
            except KeyboardInterrupt:
                pass
