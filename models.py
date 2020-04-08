import peewee as pw

from playhouse.hybrid import hybrid_property

from json import loads as json_loads, dumps as json_dumps

from .config import config

db = pw.SqliteDatabase(config['database_path'])


class BaseModel(pw.Model):

    def set(self, name: str, value: object, save: bool = True):
        self.__setattr__(name, value)
        if save: self.save()
        return self

    def toggle(self, name: str, save: bool = True):
        self.__setattr__(name, not self.__getattribute__(name))
        if save: self.save()
        return self


class User(BaseModel):
    uid = pw.IntegerField(primary_key=True)

    username = pw.TextField()

    registered = pw.BooleanField(default=False)
    verified = pw.BooleanField(default=False)
    blocked = pw.BooleanField(default=False)
    admin = pw.BooleanField(default=False)

    raw_path = pw.TextField(default='')
    raw_temp = pw.TextField(default='{}')

    class Meta:
        database = db
        db_table = 'users'

    @hybrid_property
    def path(self):
        return self.raw_path.split('|')

    @hybrid_property
    def temp(self):
        return json_loads(self.raw_temp)

    @path.setter
    def path_setter(self, new_path: list):
        self.raw_path = '|'.join(new_path)

    def set_path(self, new_path: list, save: bool = True):
        self.set('path', new_path, save)

    @temp.setter
    def temp_setter(self, obj: object):
        self.raw_temp = json_dumps(obj)

    def temp_name(self, name: object):
        return self.temp[name]

    def set_temp_name(self, name: object, value: object, save: bool = True):
        temp = self.temp
        temp[name] = value
        return self.set('temp', temp, save=save)

    def append_temp_name(self, name: object, value: object, save: bool = True):
        temp = self.temp
        if not name in temp: temp[name] = []
        temp[name].append(value)
        return self.set('temp', temp, save=save)

    def update_temp_name(self, name: object, value: object, save: bool = True):
        temp = self.temp
        if not name in temp: temp[name] = {}
        temp[name].update(value)
        return self.set('temp', temp, save=save)

    def del_temp_name(self, name: object, save: bool = True, get: bool = False):
        temp = self.temp
        if get: ret = temp[name]
        if name in temp: del temp[name]
        sel = self.set('temp', temp, save=save)
        return ret if get else sel

    def del_temp_dict_name(self, name: object, subname: object, save: bool = True, get: bool = False):
        temp = self.temp
        if get: ret = temp[name][subname]
        if name in temp and subname in temp[name]: del temp[name][subname]
        sel = self.set('temp', temp, save=save)
        return ret if get else sel


