
from telebot import types as teletypes

from .types import Node, Redirect, BaseContext

from ast import literal_eval

import texts


class MenuNode(Node):
  def __init__(self, init, back=None, markup_scheme: list = None, markup: teletypes.ReplyKeyboardMarkup = None):
    
    self.init = init

    self.back = back

    self.markup_scheme = markup_scheme

    self.markup = markup

    self.opt_check = lambda opt, ctx: True

    self.options = {}

    super().__init__()

  def set_opt_check(self, func):
    self.opt_check = func

    return self

  def add_options(self, *options):
    for option in options:
      self.options[option[0]] = option[1]

    return self

  def gen_markup(self, ctx: BaseContext):
    if not self.markup:

      gen = (opt for opt in ([opt for opt in list(self.options.keys()) if self.opt_check(opt, ctx)] + ([texts.back] if self.back else [])))

      markup = teletypes.ReplyKeyboardMarkup()

      for sc in self.markup_scheme:
        try:
          markup.row(*(next(gen) for _ in range(sc)))
        except: pass
      
      try:
        markup.add(next(gen))
      except: pass
    
    return markup

  def init_func(self, ctx: BaseContext):
    ctx.set_markup(self.gen_markup(ctx))
    
    return init(ctx) if callable(init := self.init) else ctx.send_msg(str(init), default_markup=True)

  def func(self, ctx: BaseContext):
    ctx.set_markup(self.gen_markup(ctx))

    if (back := self.back) and ctx.text == texts.back:
      return back(ctx) if callable(back) else back

    elif ctx.text in self.options:
      return opt(ctx) if callable(opt := self.options[ctx.text]) else opt

    else:
      return self.init_func(ctx)


class FormNode(Node):
  def __init__(self, final, init=None, back=None):
    self.final = final

    self.init = init
    self.back = back

    self.markup = teletypes.ReplyKeyboardMarkup().row(texts.back) if back else teletypes.ReplyKeyboardRemove()
  
    self.questions = []

    super().__init__()

  def add_questions(self, *questions):
    self.questions.extend(questions)

    return self

  def send_question(self, qid: int, ctx: BaseContext, ans: str = None, no_ans: bool = False):

    question = self.questions[qid]

    ctx.send_msg(question[0], default_markup=True)

    return Redirect.create_update_params(
      ctx,
      qid=qid,
      answers=(
        (
          ctx.params['answers'] if 
            'answers' in ctx.params else 
          []
        ) +
        (
          [ans] if not no_ans or ans else []
        )
      )
    ).no_exc()

  def init_func(self, ctx: BaseContext):
    
    ctx.set_markup(self.markup)

    if (init := self.init): init(ctx) if callable(init) else ctx.send_msg(init, default_markup=True)

    return self.send_question(0, ctx, no_ans=True)

  def func(self, ctx: BaseContext):

    ctx.set_markup(self.markup)

    try:
      qid = ctx.params['qid']
    except KeyError:
      return self.init_func(ctx)
    
    if (back := self.back) and ctx.text == texts.back: return back(ctx) if callable(back) else back

    try:
      question = self.questions[qid]
    except IndexError:
      return self.init_func
    
    if resp := question[1](ctx):
      ctx.send_msg(resp, default_markup=True)

      return self.send_question(qid, ctx, no_ans=True)
    
    entry = question[2](ctx) if len(question) == 3 else ctx.text
    
    if qid + 1 == len(self.questions):
      return self.final(
        ctx.set_params(
          answers=ctx.params['answers'] + [entry]
        )
      )
    
    return self.send_question(
      qid + 1,
      ctx,
      ans=entry
    )


class BooleanNode(Node):
  def __init__(self, init, true, false, true_field: str = texts.true_field, false_field : str = texts.false_field, final=None, back=None, false_first: bool = False, row_width: int = 2):
    self.init = init

    self.final = final

    self.back = back

    self.true = true
    self.false = false

    self.true_field = true_field
    self.false_field = false_field

    self.false_first = false_first

    self.row_width = row_width

    super().__init__()

  def markup(self):
    markup = teletypes.ReplyKeyboardMarkup(row_width=self.row_width)

    markup.add(
      *(
        (self.true_field, self.false_field) if 
          not self.false_first else 
        (self.false_field, self.true_field)
      )
    )
    
    if self.back: markup.row(texts.back)

    return markup

  def init_func(self, ctx: BaseContext):

    ctx.set_markup(self.markup())

    return self.init(ctx) if callable(self.init) else ctx.send_msg(self.init, default_markup=True)

  def func(self, ctx: BaseContext):

    if (back := self.back) and ctx.text == texts.back:
      return back(ctx) if callable(back) else back


    if ctx.text == self.true_field:
      ctx.set_params(answer=True)
      func = self.true

    elif ctx.text == self.false_field:
      ctx.set_params(answer=False)
      func = self.false

    else:
      return self.init_func(ctx)

    if (final := self.final): final(ctx)

    return func(ctx) if callable(func) else func


class ListNode(Node):
  def __init__(self, options_gen, init, final=None, back=None, empty_list=None, row_width: int = 2):

    self.options_gen = options_gen

    self.init = init

    self.final = final

    self.back = back

    self.empty_list = empty_list

    self.row_width = row_width

    super().__init__()

  def options(self, ctx: BaseContext):
    return options_gen(ctx) if callable(options_gen := self.options_gen) else options_gen

  def markup(self, ctx: BaseContext):
    markup = teletypes.ReplyKeyboardMarkup(row_width=self.row_width)

    markup.add(*(opts := [str(opt) for opt in self.options(ctx).keys()]))

    if self.back: markup.row(texts.back)

    if len(opts) == 0 and (empty_list := self.empty_list): 
      empty_list(ctx) if callable(empty_list) else ctx.send_msg(empty_list, reply_markup=markup)

    return markup

  def init_func(self, ctx: BaseContext):

    ctx.set_markup(self.markup(ctx))

    return init(ctx) if callable(init := self.init) else ctx.send_msg(init, default_markup=True)

  def func(self, ctx: BaseContext):
    options = self.options(ctx)

    if (back := self.back) and ctx.text == texts.back:
      return back(ctx) if callable(back) else back

    if not ctx.text in (str(opt) for opt in options.keys()):
      return self.init_func(ctx)

    if (final := self.final): final(ctx.set_params(answer=ctx.text))

    return option(ctx) if callable(option := options[ctx.text]) else option

class CheckListNode(ListNode):
  def __init__(self, options_gen, init, done=None, back=None, empty_list=None, row_width: int = 2):
    super().__init__(
      options_gen=options_gen,
      init=init,
      back=back,
      empty_list=empty_list,
      row_width=row_width
    )

    self.done = done

  def markup(self, ctx: BaseContext):
    
    markup = teletypes.ReplyKeyboardMarkup(row_width=self.row_width)


    markup.add(
      *(opts := [key + (texts.emoji_yes if val[0](ctx.set_params(option=key)) else texts.emoji_no) for key, val in self.options(ctx).items()])
    )

    if self.done: markup.row(texts.done)
    if self.back: markup.row(texts.back)

    if len(opts) == 0 and (empty_list := self.empty_list): 
      empty_list(ctx) if callable(empty_list) else ctx.send_msg(empty_list, reply_markup=markup)

    return markup

  def func(self, ctx: BaseContext):

    options = self.options(ctx)

    if (back := self.back) and ctx.text == texts.back:
      return back(ctx) if callable(back) else back

    if (done := self.done) and ctx.text == texts.done:
      return done(ctx) if callable(done) else done


    if len(ctx.text) > len(texts.emoji_yes) and (option := ctx.text[:-(len(texts.emoji_yes))]) in (str(opt) for opt in options.keys()):
      options[option][1](ctx.set_params(option=option))

    return self.init_func(ctx)


class NumSelectorNode(Node):
  def __init__(self, changers: list, getter, setter, init, final=None, back=None, check=None, markup_scheme: list = None, minus_first: bool = True):

    self.changers = changers

    self.getter = getter
    self.setter = setter

    self.init = init

    self.final = final
    self.back = back

    self.check = check

    self.markup_scheme = markup_scheme

    self.minus_first = minus_first
    
    super().__init__()
  
  def markup(self, ctx: BaseContext):

    gen = (str(item) for item in (
      (
        ['-' + str(changer) for changer in self.changers] if self.minus_first else ['+' + str(changer) for changer in self.changers]
      ) + 
      [self.getter(ctx)] + 
      (
        ['-' + str(changer) for changer in self.changers] if not self.minus_first else ['+' + str(changer) for changer in self.changers]
      )
    ))

    markup = teletypes.ReplyKeyboardMarkup()

    for sc in self.markup_scheme:
      try:
        markup.row(*(next(gen) for _ in range(sc)))
      except: pass
    
    try:
      markup.add(next(gen))
    except: pass

    if self.final: markup.row(texts.done)
    if self.back: markup.row(texts.back)
    
    return markup

  def init_func(self, ctx: BaseContext):
    ctx.set_markup(self.markup(ctx))

    return init(ctx) if callable(init := self.init) else ctx.send_msg(str(init), default_markup=True)

  def func(self, ctx: BaseContext):

    if (final := self.final) and ctx.text == texts.done:
      return final(ctx) if callable(final) else final

    if (back := self.back) and ctx.text == texts.back:
      return back(ctx) if callable(back) else back

    num = ctx.text.replace(' ', '')

    if num[1:].isdigit():

      num = self.getter(ctx) + literal_eval(num)

      ctx.set_params(num=num)

      if (check := self.check) and (resp := check(ctx)):
        ctx.send_msg(resp)

      else:
        self.setter(ctx, num)

    return self.init_func(ctx)

    



