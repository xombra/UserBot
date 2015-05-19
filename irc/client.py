# -*- coding: utf-8 -*-

import textwrap
import thread
import socket
import buffer
import struct
import Queue
import time
import ssl
import six

from util import always_iterable
from system import logs
from system.config import config

buffer_input = Queue.Queue()


class server(object):
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    buffer_output = buffer.LineBuffer()
    connected = False

    def __init__(self, name, server, port, _ssl, nick, sasl, pchan):
        self.name = name.lower()
        self.server = server
        self.port = port
        self.nickname = nick
        self.sasl = sasl
        self.ssl = _ssl
        self.pchan = pchan

        if not self.name in config['SVLS']:
            config['SVLS'][self.name] = {'SSL': _ssl, 'SERV': server,
                                         'PORT': port, 'SASL': sasl,
                                         'NICK': nick, 'CHAN': [],
                                         'PCHAN': pchan}

    def connect(self):
        if self.connected:
            return logs.error('%s: Ya se encuentra conectado a %s' % (__name__, self.server))

        self.socket.connect((self.server, self.port))
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

        self.connected = True
        thread.start_new(self.process_output, ())
        thread.start_new(self.process_input, ())
        self.nick(self.nickname)
        self.user(config['VERSION'], self.nickname)

        if self.sasl:
            self.socket.send('CAP REQ : sasl\r\n')
            self.socket.send('AUTHENTICATE PLAIN\r\n')
            self.socket.send('AUTHENTICATE ' + ('%s\0%s\0%s' % (
                                                                self.nickname,
                                                                self.nickname,
                                                                self.sasl)
                                                ).encode('base64') + '\r\n'
                            )
            self.socket.send('CAP END\r\n')

        time.sleep(9)
        self.join(self.pchan)

        for rejoin in config['SVLS'][self.name]['CHAN']:
            self.join(rejoin)
        logs.info("%s: Connect server=%s, port=%s, sasl=%s, ssl=%s" % (__name__, self.server, self.port, bool(self.sasl), self.ssl))

    def disconnect(self, msg='', purge=False):
        self.quit(config['VERSION'] if msg is '' else msg)
        time.sleep(2.474)
        self.socket.close()
        self.connected = False
        self.socket = socket.socket()
        logs.info("%s: Disconnect server=%s" % (__name__, self.server))

        if purge:
            del config['SVLS'][self.name]

    def reconnect(self):
        self.disconnect(config['VERSION'] + ' this reconnecting...')
        self.connect()

    def process_output(self):
        logs.info('%s: Inicio el sistema de envio de mensajes, Network: %s' % (__name__, self.name))
        while self.connected:
            for berk in self.buffer_output.lines():
                if config['SPT']:
                    logs.debug(__name__ + ': SEND <<< ' + berk)
                self.socket.send('%s\r\n' % berk)
                time.sleep(config['FLOOD PROTECTION'])

        logs.warning('%s: Se detuvo el sistema de envio de mensajes, Network: %s' % (__name__, self.name))
        thread.exit()

    def process_input(self):
        logs.info('%s: Inicio el sistema de recepcion de mensajes, Network: %s' % (__name__, self.name))
        while self.connected:
            for berk in self.socket.recv(1024).splitlines():
                if berk.find('PING', 0, 4) != -1:
                    if config['DEBUG']:
                        logs.debug('%s: PONG %s' % (__name__, berk.split()[1]))
                    self.socket.send('PONG %s\r\n' % berk.split()[1])
                else:
                    try:
                        recv = berk.split(':', 2)
                        self.nm = NickMask(recv[1].split()[0])
                        self.use = recv[1].split()[1:]
                        buffer_input.put({'self': self,
                                          'msg': recv[2]})

                        if config['SPT']:
                            logs.debug(__name__ + ': RECV >>> ' + berk)
                    except IndexError:
                        pass

        logs.warning('%s: Se detuvo el sistema de recepcion de mensajes, Network: %s' % (__name__, self.name))
        thread.exit()

    def action(self, target, action):
        """Send a CTCP ACTION command."""
        self.ctcp("ACTION", target, action)

    def admin(self, server=""):
        """Send an ADMIN command."""
        self.send_raw(" ".join(["ADMIN", server]).strip())

    def cap(self, subcommand, args=None):
        """
        Send a CAP command according to `the spec
        <http://ircv3.atheme.org/specification/capability-negotiation-3.1>`_.

        Arguments:

            subcommand -- LS, LIST, REQ, ACK, CLEAR, END
            args -- capabilities, if required for given subcommand

        Example:

            .cap('LS')
            .cap('REQ', 'multi-prefix', 'sasl')
            .cap('END')
        """
        __cap__ = ['LS', 'LIST', 'REQ', 'ACK', 'NAK', 'CLEAR', 'END']

        if subcommand in __cap__ and args is None:
            self.send_raw('CAP ' + subcommand)
        elif subcommand in __cap__ and args is not None:
            self.send_raw('CAP %s : %s' % (subcommand, args))

        #assert subcommand in client_subcommands, "invalid subcommand"

    def ctcp(self, ctcptype, target, parameter=""):
        """Send a CTCP command."""
        ctcptype = ctcptype.upper()
        tmpl = (
            "\001{ctcptype} {parameter}\001" if parameter else
            "\001{ctcptype}\001"
        )
        self.privmsg(target, tmpl.format(**vars()))

    def ctcp_reply(self, target, parameter):
        """Send a CTCP REPLY command."""
        self.notice(target, "\001%s\001" % parameter)

    def delete_channel(self, channel):
        config['SVLS'][self.name]['CHAN'].remove(channel.lower())

    def denied(self, nick, msg):
        self.privmsg(nick, 'Permiso Denegado: ' + msg)

    def globops(self, text):
        """Send a GLOBOPS command."""
        self.send_raw("GLOBOPS :" + text)

    def inchannel(self, channel):
        return channel.lower() in config['SVLS'][self.name]['CHAN']

    def info(self, server=""):
        """Send an INFO command."""
        self.send_raw(" ".join(["INFO", server]).strip())

    def invite(self, nick, channel):
        """Send an INVITE command."""
        self.send_raw(" ".join(["INVITE", nick, channel]).strip())

    def ison(self, nicks):
        """Send an ISON command.

        Arguments:

            nicks -- List of nicks.
        """
        self.send_raw("ISON " + " ".join(nicks))

    def join(self, channel, key=""):
        """Send a JOIN command."""
        if not channel in config['SVLS'][self.name]['CHAN']:
            config['SVLS'][self.name]['CHAN'].append(channel.lower())
        self.send_raw("JOIN %s%s" % (channel, '' if key else ' :' + key))

    def kick(self, channel, nick, comment=""):
        """Send a KICK command."""
        tmpl = "KICK {channel} {nick}"
        if comment:
            tmpl += " :{comment}"
        self.send_raw(tmpl.format(**vars()))

    def links(self, remote_server="", server_mask=""):
        """Send a LINKS command."""
        command = "LINKS"
        if remote_server:
            command = command + " " + remote_server
        if server_mask:
            command = command + " " + server_mask
        self.send_raw(command)

    def list(self, channels=None, server=""):
        """Send a LIST command."""
        command = "LIST"
        channels = ",".join(always_iterable(channels))
        if channels:
            command += ' ' + channels
        if server:
            command = command + " " + server
        self.send_raw(command)

    def lusers(self, server=""):
        """Send a LUSERS command."""
        self.send_raw("LUSERS" + (server and (" " + server)))

    def mode(self, target, command):
        """Send a MODE command."""
        self.send_raw("MODE %s %s" % (target, command))

    def motd(self, server=""):
        """Send an MOTD command."""
        self.send_raw("MOTD" + (server and (" " + server)))

    def names(self, channels=None):
        """Send a NAMES command."""
        tmpl = "NAMES {channels}" if channels else "NAMES"
        channels = ','.join(always_iterable(channels))
        self.send_raw(tmpl.format(channels=channels))

    def nick(self, newnick):
        """Send a NICK command."""
        self.send_raw("NICK " + newnick)

    def notice(self, target, text):
        """Send a NOTICE command."""
        # Should limit len(text) here!
        self.send_raw("NOTICE %s :%s" % (target, text))

    def notify(self, msg):
        self.send_raw('PRIVMSG %s : %s' % (self.pchan, msg))

    def oper(self, nick, password):
        """Send an OPER command."""
        self.send_raw("OPER %s %s" % (nick, password))

    def part(self, channels, message=""):
        """Send a PART command."""
        channels = always_iterable(channels)
        cmd_parts = [
            'PART',
            ','.join(channels),
        ]
        if message: cmd_parts.append(message)
        else: cmd_parts.append(config['VERSION'])
        self.send_raw(' '.join(cmd_parts))

    def pass_(self, password):
        """Send a PASS command."""
        self.send_raw("PASS " + password)

    def ping(self, target, target2=""):
        """Send a PING command."""
        self.send_raw("PING %s%s" % (target, target2 and (" " + target2)))

    def pong(self, target, target2=""):
        """Send a PONG command."""
        self.send_raw("PONG %s%s" % (target, target2 and (" " + target2)))

    def privmsg(self, target, text):
        """Send a PRIVMSG command."""
        self.send_raw("PRIVMSG %s :%s" % (target, text))

    def privmsg_many(self, targets, text):
        """Send a PRIVMSG command to multiple targets."""
        target = ','.join(targets)
        return self.privmsg(target, text)

    def quit(self, message=""):
        """Send a QUIT command."""
        # Note that many IRC servers don't use your QUIT message
        # unless you've been connected for at least 5 minutes!
        self.send_raw("QUIT" + (message and (" :" + message)))

    def send_raw(self, msg):
        msg = msg.decode(config['ENCODE']) + '\r\n'
        msg = (textwrap.wrap(msg, 502)[0] + '...\r\n') if len(msg) > 502 else msg
        self.buffer_output.feed(msg)

    def squit(self, server, comment=""):
        """Send an SQUIT command."""
        self.send_raw("SQUIT %s%s" % (server, comment and (" :" + comment)))

    def std(self, target, text):
        self.send_raw("PRIVMSG %s :%s" % (target, text))

    def stats(self, statstype, server=""):
        """Send a STATS command."""
        self.send_raw("STATS %s%s" % (statstype, server and (" " + server)))

    def time(self, server=""):
        """Send a TIME command."""
        self.send_raw("TIME" + (server and (" " + server)))

    def topic(self, channel, new_topic=None):
        """Send a TOPIC command."""
        if new_topic is None:
            self.send_raw("TOPIC " + channel)
        else:
            self.send_raw("TOPIC %s :%s" % (channel, new_topic))

    def trace(self, target=""):
        """Send a TRACE command."""
        self.send_raw("TRACE" + (target and (" " + target)))

    def user(self, username, realname):
        """Send a USER command."""
        self.send_raw("USER %s 0 * :%s" % (username, realname))

    def userhost(self, nicks):
        """Send a USERHOST command."""
        self.send_raw("USERHOST " + ",".join(nicks))

    def users(self, server=""):
        """Send a USERS command."""
        self.send_raw("USERS" + (server and (" " + server)))

    def version(self, server=""):
        """Send a VERSION command."""
        self.send_raw("VERSION" + (server and (" " + server)))

    def wallops(self, text):
        """Send a WALLOPS command."""
        self.send_raw("WALLOPS :" + text)

    def who(self, target="", op=""):
        """Send a WHO command."""
        self.send_raw("WHO%s%s" % (target and (" " + target), op and (" o")))

    def whois(self, targets):
        """Send a WHOIS command."""
        self.send_raw("WHOIS " + ",".join(always_iterable(targets)))

    def whowas(self, nick, max="", server=""):
        """Send a WHOWAS command."""
        self.send_raw("WHOWAS %s%s%s" % (nick,
                                         max and (" " + max),
                                         server and (" " + server)))

def is_channel(string):
    """Check if a string is a channel name.

    Returns true if the argument is a channel name, otherwise false.
    """
    return string and string[0] in "#&+!"

def ip_numstr_to_quad(num):
    """
    Convert an IP number as an integer given in ASCII
    representation to an IP address string.

    >>> ip_numstr_to_quad('3232235521')
    '192.168.0.1'
    >>> ip_numstr_to_quad(3232235521)
    '192.168.0.1'
    """
    n = int(num)
    packed = struct.pack('>L', n)
    bytes = struct.unpack('BBBB', packed)
    return ".".join(map(str, bytes))

def ip_quad_to_numstr(quad):
    """
    Convert an IP address string (e.g. '192.168.0.1') to an IP
    number as a base-10 integer given in ASCII representation.

    >>> ip_quad_to_numstr('192.168.0.1')
    '3232235521'
    """
    bytes = map(int, quad.split("."))
    packed = struct.pack('BBBB', *bytes)
    return str(struct.unpack('>L', packed)[0])

class NickMask(six.text_type):
    """
    A nickmask (the source of an Event)

    >>> nm = NickMask('pinky!username@example.com')
    >>> print(nm.nick)
    pinky

    >>> print(nm.host)
    example.com

    >>> print(nm.user)
    username

    >>> isinstance(nm, six.text_type)
    True

    >>> nm = 'красный!red@yahoo.ru'
    >>> if not six.PY3: nm = nm.decode('utf-8')
    >>> nm = NickMask(nm)

    >>> isinstance(nm.nick, six.text_type)
    True

    Some messages omit the userhost. In that case, None is returned.

    >>> nm = NickMask('irc.server.net')
    >>> print(nm.nick)
    irc.server.net
    >>> nm.userhost
    >>> nm.host
    >>> nm.user
    """
    @classmethod
    def from_params(cls, nick, user, host):
        return cls('{nick}!{user}@{host}'.format(**vars()))

    @property
    def nick(self):
        nick, sep, userhost = self.partition("!")
        return nick.encode(config['ENCODE'])

    @property
    def userhost(self):
        nick, sep, userhost = self.partition("!")
        return userhost.encode(config['ENCODE']) or None

    @property
    def host(self):
        nick, sep, userhost = self.partition("!")
        user, sep, host = userhost.partition('@')
        return host.encode(config['ENCODE']) or None

    @property
    def user(self):
        nick, sep, userhost = self.partition("!")
        user, sep, host = userhost.partition('@')
        return user.encode(config['ENCODE']) or None
