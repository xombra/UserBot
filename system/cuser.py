# -*- coding: utf-8 -*-
import sqlite3
import config
import logs
import time
from uuid import *

try:
    exec "from hashlib import %s as hash" % config.config["HASH"]
except ImportError as error:
    exit(chr(27)+"[1;31m"+error+chr(27)+"[0m")

"""
+---------------------------Modulo de base de datos----------------------------+
|    Base de Datos: Usuarios                                                   |
|    Ejemplo de uso:                                                           |
| >>> import system.cuser                                                      |
| >>> db = = system.cuser.cuser()                                              |
| >>> db.register('nickname', 'password')                                      |
| >>> db.userinfo('nickname')                                                  |
|     {'status': None, 'password': u'b109f3bbbc244eb82441917ed06d618b9008dd09b |
|     3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95 |
|     385ffab0cacbc86', 'nickname': u'nickname', 'uuid': u'd31a122a-cbfe-521b- |
|     9762-d78568e1d006'}                                                      |
| >>> db.update({'nickname': 'nick'}, 'nickname')                              |
| >>> db.userinfo('nick')                                                      |
|     {'status': None, 'password': u'b109f3bbbc244eb82441917ed06d618b9008dd09b |
|     3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95 |
|     385ffab0cacbc86', 'nickname': u'nick', 'uuid': u'f269cafb-580d-5776-bbd7 |
|     -984c6b6b692e'}                                                          |
| >>> db.remove('nick')                                                        |
| >>> db.userinfo('nick')                                                      |
|                                                                              |
|    NOTA:  El estatus sera unicamente usado para la autenticar a algun usuario|
|    y determinar su estado, online u offline, solo pudiendo ser remplazado por|
|    el estatus de root, otorgado unicamente a los administradores del bot.    |
|                                                                              |
+------------------------------------------------------------------------------+
"""


class cuser(object):

    def __init__(self):

        self.__auth__ = {}
        self.con = sqlite3.connect("db/cuser.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS cuser (
                uuid text,
                nickname text,
                password text,
                status text)""")

    def register(self, nickname, password):

        UUID = str(uuid5(NAMESPACE_DNS, nickname.lower()))
        password = hash(password).hexdigest()

        self.cur.execute("""
            insert into cuser (
                uuid,
                nickname,
                password
            )
            values(
                '%s',
                '%s',
                '%s'
            )""" % (UUID, nickname, password))
        self.con.commit()
        logs.info("%s: New User %s" % (__name__, nickname))


    def update(self, kw, im):
        """ Esta funcion requiere que el argumento sea <type 'dict'> para tomar
            el par {CLAVE: VALOR} y asi actualizar."""

        if "password" in kw:
            kw["password"] = hash(kw["password"]).hexdigest()

        if "nickname" in kw:
            kw["uuid"] = str(uuid5(NAMESPACE_DNS, kw["nickname"].lower()))

        for u in kw.keys():
            self.cur.execute("""
                update cuser set %s='%s' where uuid='%s'
                """ % (u, kw[u], str(uuid5(NAMESPACE_DNS, im.lower()))))

        self.con.commit()
        logs.info("%s: %s update %s" % (__name__, im, str(kw.keys())))

    def userinfo(self, im, uuid=''):
        if uuid == '':
            uuid = str(uuid5(NAMESPACE_DNS, im.lower()))

        self.cur.execute("select * from cuser where uuid='%s'" % uuid)

        for u in self.cur.fetchall():
            return {"uuid": u[0], "nickname": u[1], "password": u[2], "status": u[3]}

    def remove(self, im):
        uuid = str(uuid5(NAMESPACE_DNS, im.lower()))
        self.cur.execute("delete from cuser where uuid='%s'" % (uuid,))
        self.con.commit()
        logs.info("%s: Delete user %s" % (__name__, im))

    def hasher(string):
        return hash(string).hexdigest()

    def auth(self, irc, password):
        info = self.userinfo(irc.nm.nick)
        password = hash(password).hexdigest()

        if not irc.name in self.__auth__:
            self.__auth__[irc.name] = {}

        if password == info['password']:
            self.__auth__[irc.name].update({irc.nm.host: time.time()})
            self.update({'status': 'online'}, irc.nm.nick)
            irc.privmsg(irc.nm.nick, 'Ha sido autenticado bajo: ' + irc.nm.host)
        else:
            irc.denied(irc.nm.nick, 'Usuario / Contraseña erronea ᕦ(ò_ó)ᕤ')

    def isauth(self, irc):
        info = self.userinfo(irc.nm.nick)

        try:
            if info['status'] in ('offline', None):
                irc.denied(irc.nm.nick, 'Autentíquese.')
                return False
        except TypeError:
            irc.denied(irc.nm.nick, 'Registrese.')
            return False

        if not irc.name in self.__auth__:
            self.__auth__[irc.name] = {}

        if info['status'] in ('online', 'oper'):
            if info['status'] is 'oper':
                return True
            if irc.nm.host in self.__auth__[irc.name]:
                time_ = time.time() - self.__auth__[irc.name][irc.nm.host]

                if time_ >= config.config['TIMEOUT']:
                    self.update({'status': 'offline'}, irc.nm.nick)
                    irc.denied(irc.nm.nick, 'Autentíquese.')
                else:
                    self.__auth__[irc.name].update({irc.nm.host: time.time()})
                    return True
            else:
                irc.denied(irc.nm.nick, 'Cuenta usurpada.')
        return False

cuser = cuser()