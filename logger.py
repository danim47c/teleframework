from colorama import Fore

from datetime import datetime

from traceback import format_exc


class Logger(object):
    debug_base = '{color}   [DEBUG][{time}] {msg}'
    info_base = '{color}    [INFO][{time}] {msg}'
    warning_base = '{color} [WARNING][{time}] {msg}'
    error_base = '{color}   [ERROR][{time}] {msg}'
    error_base_e = '{color}   [ERROR][{time}] {msg} | Error: [\n{error}\n]'
    critical_base = '{color}[CRITICAL][{time}] {msg}'
    critical_base_e = '{color}[CRITICAL][{time}] {msg} | Error: [\n{error}\n]'

    def __init__(self, path: str, level: int = 0, file_log: bool = True):
        self.path = path

        self.level = level

        self.file_log = file_log

    @property
    def time(self):
        return datetime.now().strftime(r'%d/%m/%Y %H:%M:%S:%f')

    def log(self, msg: str, msg_nc: str = None):
        print(msg + Fore.RESET)

        if self.file_log:
            with open(self.path, 'a') as file: file.write(msg_nc + '\n')

    def debug(self, msg: str):
        if self.level <= 1:
            self.log(
                self.debug_base.format(
                    color=Fore.LIGHTBLUE_EX,
                    time=self.time,
                    msg=msg
                ),
                self.debug_base.format(
                    color='',
                    time=self.time,
                    msg=msg
                )
            )

    def info(self, msg: str):
        if self.level <= 2:
            self.log(
                self.info_base.format(
                    color=Fore.GREEN,
                    time=self.time,
                    msg=msg
                ),
                self.info_base.format(
                    color='',
                    time=self.time,
                    msg=msg
                )
            )

    def warning(self, msg: str):
        if self.level <= 3:
            self.log(
                self.warning_base.format(
                    color=Fore.YELLOW,
                    time=self.time,
                    msg=msg
                ),
                self.warning_base.format(
                    color='',
                    time=self.time,
                    msg=msg
                )
            )

    def error(self, msg: str, error=True):
        if self.level <= 4:
            base = self.error_base if not error else self.error_base_e
            self.log(
                base.format(
                    color=Fore.BLUE,
                    time=self.time,
                    msg=msg,
                    error='' if not error else '    ' + '\n    '.join(format_exc().split('\n')[:-1])
                ),
                base.format(
                    color='',
                    time=self.time,
                    msg=msg,
                    error='' if not error else '    ' + '\n    '.join(format_exc().split('\n')[:-1])
                )
            )

    def critical(self, msg: str = None, error=True):
        if self.level <= 5:
            base = self.critical_base if not error else self.critical_base_e
            self.log(
                base.format(
                    color=Fore.RED,
                    time=self.time,
                    msg=msg,
                    error='' if not error else '    ' + '\n    '.join(format_exc().split('\n')[:-1])
                ),
                base.format(
                    color='',
                    time=self.time,
                    msg=msg,
                    error='' if not error else '    ' + '\n    '.join(format_exc().split('\n')[:-1])
                )
            )