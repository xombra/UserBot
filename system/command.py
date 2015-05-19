# -*- coding: utf-8 -*-
import re
import sys
import logs
import thread

from config import config
from irc.client import buffer_input


class core(object):

    def __init__(self, ):
        self.ls = []
        thread.start_new(self.endless, ())

    def commandHandler(self, base, sub={}, mod=''):
        """
        Argumentos:
            sub -- Diccionario con sub-valores:
                                     regex -- Expresion regular
                                     function -- Funcion a ejecutar
            base -- Es usado para la base del comando, y asi poder destinguir
                    sub-comandos en caso de que existan.
        """

        if len(sub) == 0:
            self.ls.append({'base': re.compile(base, 2), 'command': [], 'mod': mod})
        else:
            for q in self.ls:
                if q['base'] == re.compile(base, 2):
                    sub.update({'regex': re.compile(sub['regex'], 2)})
                    return self.ls[self.ls.index(q)]['command'].append(sub)

    def removeHandler(self, mod):
        for one in self.ls:
            if one['mod'] is mod:
                self.ls.remove(one)


    def likely(self, string):
        """
        Retorna lista con las probables cadenas que contengan comandos.
        Arumengto:
            string -- Cadena contenedora de los comandos probables
        """

        possible = []
        string = string.replace(config['PRE'], '{0}ꟿ{0}'.format(config['PRE']))
        string = string.split(config['PRE'])
        for q in range(len(string)):
            try:
                possible.append(string[string.index('ꟿ') + 1])
                del string[string.index('ꟿ')]
            except (IndexError, ValueError):
                pass

        return possible

    def command(self, string):
        for one in self.ls:
            if one['base'].match(string):
                for two in one['command']:
                    if two['regex'].match(string):
                        return {'regex': two['regex'].match(string),
                                'function': two['function']}

    def endless(self):
        while not config['ABORT']:
            buffer = buffer_input.get()   # lint:ok
            likely = self.likely(buffer['msg'])
            for unit in likely:
                if config['DEBUG']:
                    logs.info('%s: Posible comando procesado: %s' % (__name__, unit))
                unit = self.command(unit)
                try:
                    if unit is not None:
                        unit['function'](buffer['self'], unit['regex'])
                except NameError:
                    error = sys.exc_info()
                    logs.error('%s: Unexpected error %s %s' % (__name__, error[0], error[1]))
        logs.warning('%s: No se estan procesando los comandos.' % __name__)

core = core()