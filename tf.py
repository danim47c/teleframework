
from .config import config

from telebot import TeleBot as TelegramBot, types as teletypes

from .logger import Logger

from .types import MainNode, MessageContext, CallbackContext, Redirect, Node

from timeloop import Timeloop

from datetime import datetime

import logging

import texts


class TeleFramework(object):
  def __init__(self, default_path: list = [''], content_types: list = ['text']):
    
    self.bot = TelegramBot(
      token=config['bot_token']
    )

    self.logger = Logger(
      path=config['logging']['path'],
      level=config['logging']['level'],
      file_log=config['logging']['file_log_enabled']
    )

    self.timeloop = Timeloop()
    self.timeloop.logger.disabled = True

    self.node = MainNode(self)

    self.paths = {}
    self.commands = {}

    self.spyders = {
      '|': []
    }

    self.default_path = default_path

    self.content_types = content_types

    self.__time_reset()

    self.__init_handlers()

  def __init_handlers(self):

    self.bot.message_handler(
      content_types=self.content_types
    )(
      self.__message_handler
    )

    self.bot.callback_query_handler(
      lambda callback: True
    )(
      self.__callback_handler
    )


  def register_path(self, path: str, func):
    self.paths[path] = func
    return self
  
  def register_command(self, command: str, func):
    self.commands[command] = func
    return self
  
  def path_decorator(self, path: str):
    def path_inner(func):
      return self.register_path(
        path=path,
        func=func
      )
    return path_inner
  
  def command_decorator(self, command: str):
    def command_inner(func):
      return self.register_command(
        command=command,
        func=func
      )
    return command_inner

  def register_spyder(self, func, paths: list = None):
    if not paths: paths = [r'|']
    elif not isinstance(paths, list): paths = list(paths)
    
    for path in paths:
      if path in (spyders := self.spyders): spyders[path].append(func)
      else: spyders[path] = [func]

    return self
  
  def spyder_decorator(self, paths: list = None):
    def spyder_inner(func):
      return self.register_spyder(
        func=func,
        paths=paths
      )
    return spyder_inner


  def add_modules(self, *modules):
    for module in modules:
      __import__(module, fromlist=('setup')).setup(self)


  def __time_dif(self):
    return (datetime.now() - self.__time)

  def __time_reset(self):
    self.__time = datetime.now()
    return self.__time

  def start(self):

    self.logger.info(
      msg=texts.logging_start.format(
        seconds=self.__time_dif().total_seconds()
      )
    )
    self.__time_reset()
    
    try:
      self.timeloop.start()
      self.bot.polling(
        none_stop=True
      )
    except KeyboardInterrupt:
      pass
    except Exception:
      self.logger.critical(
        msg=texts.logging_critical_error
      )
    finally:
      self.timeloop.stop()
      self.logger.info(
        msg=texts.logging_stop.format(
          hours=round(
            self.__time_dif().total_seconds() / 3600,
            4
          )
        )
      )

  def stop(self):
    return self.bot.stop_bot()


  def __enter__(self):
    self.logger.info(texts.logging_configure)
    
    self.__time_reset()

    return self
  
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.start()


  def __message_handler(self, message: teletypes.Message, init: bool = False):
    context = MessageContext(
      message,
      self
    )

    if init: context.set_init()

    resp = self.node.run(context)

    if isinstance(resp, Redirect):
      context.user.set_path(resp.to(context.path.path))

      if resp.exc: self.__message_handler(message, init=True)
    

  def __callback_handler(self, callback: teletypes.CallbackQuery, init: bool = False):
    context = CallbackContext(
      callback,
      self
    )

    if init: context.set_init()

    resp = self.node.run(context)

    if isinstance(resp, Redirect):
      context.user.set_path(resp.to(context.path.path))
      context.update_path()

      context.set_init()

      if resp.exc: resp = self.node.run(context)
    
    return

