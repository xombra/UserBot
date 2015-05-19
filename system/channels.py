# -*- coding: utf-8 -*-

import sqlite3
import logs
from uuid import *
from irc import modes


class channels(object):

    def __init__(self):
        self.con = sqlite3.connect('db/servers.db', check_same_thread=False)
        self.cur = self.con.cursor()

    def list(self, server, flags=''):
        """
        Listar la base de datos.
        Argumentos:
            server -- Servidor usado en las db, solo este parametro proporciona
                      la lista de canales registrados de dicho servidor.

            flags -- Se especifica un canal al cual se listaran todos los flags
                     que contenga dicho canal.
        """

        __T__ = []
        if not flags:
            T=self.cur.execute("select * from sqlite_master where type='table'")
            for table in T.fetchall():
                table = table[1].split('_')
                if table[0] == server:
                    __T__.append(table[1].replace('$', '#').lower())
        else:
            T = self.cur.execute("select * from {}_{}".format(server, flags))
            for table in T.fetchall():
                __T__.append(table[1:])

        return __T__

    def register(self, server, channel):
        if channel.startswith('#'):
            channel = server + "_" + channel.replace('#', '$')
        else:
            return

        self.cur.execute("""create table %s (
                                        uuid text primary key,
                                        nickname text not null,
                                        flags)""" % channel)
        self.con.commit()
        logs.info("%s: canal registrado %s" % (__name__, channel))

    def flags(self, server, channel, nickname, flags):
        uuid = str(uuid5(NAMESPACE_DNS, nickname.lower()))

        if channel.startswith('#'):
            chsv = server + "_" + channel.replace('#', '$')
        else:
            return

        if not self.inChannel(server, channel, nickname):
            self.cur.execute("""insert into %s (
                                    uuid,
                                    nickname
                                )

                                values (
                                    '%s',
                                    '%s')""" % (chsv, uuid, nickname))

        for parsed in modes.parse_nick_modes(flags):
            now = self.get(server, channel, nickname)
            print parsed

            if parsed[1] in 'BCFSoprtv':
                if parsed[0] == '+' and not parsed[1] in now:
                    self.cur.execute("update %s set flags='%s' where uuid='%s'" % (chsv, now + parsed[1], uuid))
                elif parsed[0] == '-' and parsed[1] in now:
                    self.cur.execute("update %s set flags='%s' where uuid='%s'" % (chsv, now.replace(parsed[1], ''), uuid))

        logs.info("%s: Set flags %s >>> %s" % (__name__, nickname, flags))
        self.con.commit()

    def _register(self, server, channel, nickname):
        self.register(server, channel)
        self.flags(server, channel, nickname, '+CFSoprtv')

    def get(self, server, channel, nickname):
        if channel.startswith('#'):
            chsv = server + "_" + channel.replace('#', '$')
        else:
            return
        uuid = str(uuid5(NAMESPACE_DNS, nickname.lower()))
        self.cur.execute('select flags from %s where uuid="%s"' % (chsv, uuid))

        for u in self.cur.fetchall():
            return u[0] if u != None else ''

    def inChannel(self, server, channel, nickname):
        if channel.startswith('#'):
            chsv = server + "_" + channel.replace('#', '$')
        else:
            return

        uuid = str(uuid5(NAMESPACE_DNS, nickname.lower()))
        self.cur.execute("select * from %s where uuid='%s'" % (chsv, uuid))
        for u in self.cur.fetchall():
            return True
        return False

    def drop(self, server, channel):
        if channel.startswith('#'):
            chsv = server + "_" + channel.replace('#', '$')
        else:
            return

        self.cur.execute('drop table if exists ' + chsv)

    def _drop(self, server):

        for i in self.list(server):
            self.cur.execute('drop table %s_%s' % (server, i.replace('#', '$')))

channels = channels()