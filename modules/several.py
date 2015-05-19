# -*- coding: utf-8 -*-

from system.command import core
from system.channels import channels
from system.cuser import cuser

import sqlite3


def register_chan(irc, regex):
    if not cuser.isauth(irc):
        return

    if not irc.inchannel(regex.group('channel')):
        irc.denied(irc.nm.nick, 'Contacte con un administrador para registrar.')
        irc.notify('[%s] intento registrar [%s]' % regex.group('channel'))

    if regex.group('channel').lower() in channels.list(irc.name):
        irc.denied(irc.nm.nick, 'Canal registrado.')
    else:
        channels._register(irc.name, regex.group('channel'), irc.nm.nick)
        irc.std(irc.nm.nick, 'Se registro el canal.')
        irc.notify('Canal registrado [%s]' % regex.group('channel'))


def drop_chan(irc, regex):
    if not cuser.isauth(irc):
        return

    if not irc.inchannel(regex.group('channel')):
        return irc.denied(irc.nm.nick, 'El canal no esta registrado')

    C = channels.get(irc.name, regex.group('channel'), irc.nm.nick)

    if not 'F' in C:
        irc.denied(irc.nm.nick, 'Flags insuficientes.')
    else:
        channels.drop(irc.name, regex.group('channel'))
        irc.delete_channel(regex.group('channel'))
        irc.part(regex.group('channel'))
        irc.privmsg(irc.nm.nick, 'Canal eliminado con exito.')
        irc.privmsg(irc.pchan,
            '%s drop chan %s' % (irc.nm.nick, regex.group('channel')))


def flags(irc, regex):
    if not cuser.isauth(irc):
        return

    if not irc.inchannel(regex.group('channel')):
        return irc.denied(irc.nm.nick, 'El canal no esta registrado')

    C = channels.get(irc.name, regex.group('channel'), irc.nm.nick)

    if not 'S' in C:
        irc.denied(irc.nm.nick, 'Flags insuficientes.')
    else:
        if cuser.userinfo(regex.group('nickname')) is not None:
            bef = channels.get(irc.name,
                               regex.group('channel'),
                               regex.group('nickname'))
            channels.flags(irc.name,
                           regex.group('channel'),
                           regex.group('nickname'),
                           regex.group('flags'))
            aft = channels.get(irc.name,
                               regex.group('channel'),
                               regex.group('nickname'))
            irc.privmsg(irc.use[1], 'Change flags [%s] >>> [%s]' % (bef, aft))
        else:
            irc.denied(irc.use[1], 'Cuenta [%s] inexistente.' % regex.group('nickname'))


def get_flags(irc, regex):
    if not cuser.isauth(irc):
        return

    if not irc.inchannel(regex.group('channel')):
        return irc.denied(irc.nm.nick, 'El canal no esta registrado')

    irc.privmsg(irc.use[1], 'ACOUNT                         FLAGS')
    if regex.group('nickname') is '[all]':
        for list in channels.list(irc.name, irc.use[1]):
            irc.privmsg(irc.use[1], '%-30s %s' % list)
    else:
        flags = channels.get(irc.name,
                             regex.group('channel'),
                             regex.group('nickname'))
        irc.privmsg(irc.use[1], '%-30s %s' % (regex.group('nickname'), flags))

chan = 'chan (register #.+|drop #.+|get #.+ .+|flags (#.+) (.+) ((\+|-).+))'
core.commandHandler(chan, mod='several')
core.commandHandler(chan, {'descrip': 'Registra un canal en la base de datos',
                           'regex': 'chan register (?P<channel>#.+)',
                           'function': register_chan})

core.commandHandler(chan, {'descrip': 'Elimina un canal de la base de datos',
                           'regex': 'chan drop (?P<channel>#.+)',
                           'function': drop_chan})

core.commandHandler(chan, {'descrip': 'Establece el nivel de privilegios de un usuario.',
                           'regex': 'flags (?P<channel>#.+) (?P<nickname>.+) (?P<flags>(\+|-).+)',
                           'function': flags})

core.commandHandler(chan, {'descrip': 'Muestra los flags de un usuario en un canal',
                           'regex': 'flags (?P<channel>#.+) (?P<nickname>.+)',
                           'function': get_flags})


def register_user(irc, regex):
    if cuser.userinfo(irc.nm.nick) is None:
        cuser.register(irc.nm.nick, regex.group('password'))
        cuser.auth(irc, regex.group('password'))
        irc.privmsg(irc.nm.nick, 'La cuenta ha sido creada. [%s] [%s]' % (irc.nm.nick, regex.group('password')))
        irc.privmsg(irc.pchan, 'Nueva cuenta: [%s]' % irc.nm.nick)
    else:
        irc.privmsg(irc.nm.nick, 'La cuenta [%s] ya existe.' % irc.nm.nick)


def drop_user(irc, regex):
    if cuser.isauth(irc):
        cuser.remove(irc.nm.nick)
        del cuser.__auth__[irc.name][irc.nm.host]
        irc.privmsg(irc.nm.nick, 'La cuenta [%s] se ha eliminado' % irc.nm.nick)
        irc.privmsg(irc.pchan, 'Cuenta eliminada: [%s]' % irc.nm.nick)


def auth(irc, regex):
    try:
        cuser.auth(irc, regex.group('password'))
    except TypeError:
        irc.denied(irc.nm.nick, 'Registrese.')


user = 'user (register .+|drop|auth .+|super .+ .+)'
core.commandHandler(user, mod='several')
core.commandHandler(user, {'descrip': 'Registra un usuario en la base de datos',
                           'regex': 'user register (?P<password>.+)',
                           'function': register_user})

core.commandHandler(user, {'descrip': 'Elimina un usuario de la base de datos',
                           'regex': 'user drop',
                           'function': drop_user})

core.commandHandler(user, {'descrip': 'Autentica a un usuario como el propietario de la cuenta.',
                           'regex': 'user auth (?P<password>.+)',
                           'function': auth})