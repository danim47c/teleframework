
from telebot import types as teletypes

from .models import User

from ast import literal_eval

import texts


class Path(object):
  def __init__(self, path: list):
    self.__path = path
    self.__n = -1

  @property
  def path(self):
      return self.__path
  
  def __str__(self):
      return r'|'.join(self.__path)
  
  def __next_num(self):
    self.__n += 1
    return self.__n

  @property
  def next_path(self):
    return self.path[self.__next_num()]
    
  @property
  def this_path(self):
    return self.path[self.__n]
  
  @property
  def last_path(self):
    return self.__n + 1 == len(self.path)

  def get_params(string: str):
    if len(string.split(r'?')) > 1:
      return {
        (splitted := param.split(r'='))[0]: literal_eval(splitted[1]) for param in string.split(r'?')[-1].split(r'&')
      }
    return {}

  def set_params(params: dict, path):
      original_params = {}

      for subpath in path:
        original_params.update(Path.get_params(subpath))

      original_params.update(params)
      return (
        r'|'.join(
          (subpath.split(r'?')[0] for subpath in path)
        ) + r'?' + 
          '&'.join(
            f'{key}={val}' for key, val in original_params.items()
        )
      ).split(r'|')


class BaseContext(object):
  def __init__(self, tf):

    self.bot = tf.bot

    self.logger = tf.logger

    self.tf = tf

    self.init = False

    self.markup = None

    self.params = {}

    self.is_command = False
    self.command = None

    self.path = None

  @property
  def chat_id(self):
    return None
  
  @property
  def text(self):
    return None
  
  @property
  def data(self):
    return None


  def send_msg(self, text: str, reply_markup: object = None, default_markup: bool = False, clear_markup: bool = False, disable_notification: bool = False, disable_web_preview: bool = False):

    markup = teletypes.ReplyKeyboardRemove() if clear_markup else reply_markup if reply_markup else self.markup if default_markup else None

    return self.bot.send_message(
      chat_id=self.chat_id,
      text=text,
      reply_markup=markup,
      disable_notification=disable_notification,
      disable_web_page_preview=disable_web_preview
    )
  
  def send_photo(self, photo: str, caption: str = None, reply_markup: object = None, default_markup: bool = False, clear_markup: bool = False, disable_notification: bool = False):

    markup = teletypes.ReplyKeyboardRemove() if clear_markup else reply_markup if reply_markup else self.markup if default_markup else None

    return self.bot.send_photo(
      chat_id=self.chat_id,
      photo=photo,
      caption=caption,
      reply_markup=markup,
      disable_notification=disable_notification
    )

  
  def set_markup(self, markup: object):
    self.markup = markup
    return self
  
  def set_params(self, **params):
    self.params.update(
      params
    )

    return self

  def update_params(self, string: str = None):
    self.params.update(
      Path.get_params(string if string else self.path.this_path)
    )
    return self

  def update_path(self):
    self.path = Path(self.user.path)
    return self

  def set_init(self):
    self.init = True
    return self

class MessageContext(BaseContext):
  def __init__(self, message: teletypes.Message, tf):

    super().__init__(tf)

    self.message = message

    if not self.message.text: self.message.text = ''

    self.user = User.get_or_create(uid=(from_user := message.from_user).id, username=from_user.username)[0]

    if (command := message.text.split(r'?')[0]) in tf.commands:

      self.is_command = True
      self.command = command

      self.update_params(self.message.text)

    self.path = Path(self.user.path)
  
  @property
  def chat_id(self):
    return self.message.chat.id

  @property
  def text(self):
    return self.message.text

class CallbackContext(BaseContext):
  def __init__(self, callback: teletypes.CallbackQuery, tf):

    super().__init__(tf)

    self.callback = callback

    self.user = User.get_or_create(uid=(from_user := callback.from_user).id, username=from_user.username)[0]

    if self.init:
      self.path = Path(self.user.path) 

    else:
      if 'command' in self.data and (command := self.data['command'].split(r'?')[0]) in tf.commands:
        self.is_command = True
        self.command = command

        self.path = Path(self.user.path)

        self.update_params(self.data['command'])
      
      elif 'path' in self.data:
        self.user.set_path(path := self.data['path'])
        self.path = Path(path)
        self.init = True

  @property
  def data(self):
    return literal_eval(self.callback.data)

  @property
  def chat_id(self):
    return self.user.uid



class Redirect(object):
  to = lambda path: path

  exc = True

  def __init__(self, to):
    self.to = to if to else self.to

  def new_path(self, path: list):
    return self.to(path)

  def create_to(to: list):
    return Redirect(lambda path: list(to))
  
  def create_back(back: int = 1):
    return Redirect(lambda path: path[:-(back)])
  
  def create_move(to: list, back: int = 1):
    return Redirect(lambda path: path[:-(back)] + list(to))
  
  def create_go(to: list, back: int = 0):
    return Redirect(lambda path: path[:len(path) - back] + list(to))
  
  def create_update_params(ctx: BaseContext, **params):
    ctx.params.update(params)
    return Redirect(lambda path: Path.set_params(ctx.params, path))

  def no_exc(self):
    self.exc = False
    return self


class Node(object):

  def __init__(self):
    self.paths = {}

    self.spyders = []

  func = lambda s, ctx: None
  init_func = lambda s, ctx: None

  def set_func(self, func):
    self.func = func
    return self
  
  def set_init_func(self, init_func):
    self.init_func = init_func
    return self
  
  def func_decorator(self):
    def func_inner(func):
      self.set_func(func)
      return func
    return func_inner

  def init_func_decorator(self):
    def init_func_inner(init_func):
      self.set_init_func(init_func)
      return init_func
    return init_func_inner
  
  
  def add_modules(self, *modules):
    for module in modules:
      __import__(module, fromlist=('setup')).setup(self)
        

  def register_spyder(self, func):
    self.spyders.append(func)
  
  def spyder_decorator(self):
    def spyder_inner(func):
      return self.register_spyder(func)
    return spyder_inner
  
  def register_path(self, path: str, func):
    self.paths[path] = func
    return self
  
  def path_decorator(self, path: str):
    def path_inner(func):
      self.register_path(path, func)
      return func
    return path_inner

  
  path_not_found = lambda s, ctx: (
    ctx.logger.warning(
      (
        texts.logging_command_not_found if ctx.is_command else (texts.logging_unreachable_path if not ctx.init else texts.logging_unreachable_path_redirected)
      ).format(
        command=ctx.command,
        path=ctx.path.path,
        point=ctx.path.this_path,
        user=ctx.user.username,
        user_id=ctx.user.uid
      )
    ),
    Redirect.create_back()
  )[-1]

  def run(self, ctx: BaseContext):
    if ctx.path.last_path:
      return (
        self.func if not ctx.init else self.init_func
      )(ctx)
    
    else:
      try:
        spyders = [spyder(ctx) for spyder in self.spyders]

        if len(spyders) != 0 and len(reds := [spyder for spyder in filter(lambda spyder: spyder != False, spyders)]) > 0:
          return reds[-1]

        next_path = self.paths[ctx.path.next_path.split(r'?')[0]]
        ctx.update_params()

      except KeyError:
        return self.path_not_found(ctx)

      return next_path(ctx) if callable(next_path) else next_path.run(ctx) if issubclass(next_path.__class__, Node) else next_path

class MainNode(Node):
  def __init__(self, tf):
    self.tf = tf

  def run(self, ctx: BaseContext):
    try:

      if not ctx.path:
        return

      if not ctx.init and ctx.is_command:
        return self.tf.commands[ctx.command](ctx)

      spyders = list(spyder(ctx) for spyder in self.tf.spyders['|'])

      spyders += list(spyder(ctx) for spyder in self.tf.spyders[first_path]) if (first_path := ctx.path.path[0]) in self.tf.spyders else []

      if len(spyders) != 0 and len(reds := [spyder for spyder in filter(lambda spyder: spyder != False, spyders)]) > 0:
        return reds[-1]

      next_path = self.tf.paths[ctx.path.next_path.split(r'?')[0]]
      ctx.update_params()

    except KeyError:
      return self.path_not_found(ctx)

    return next_path(ctx) if callable(next_path) else next_path.run(ctx) if issubclass(next_path.__class__, Node) else next_path