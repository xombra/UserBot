# -*- coding: utf-8 -*-
import cPickle
config = ['DEBUG', 'PRE', 'HASH', 'FLOOD PROTECTION', 'SPT', 'ENCODE', 'TIMEOUT']
config = dict.fromkeys(config, None)
config.update({'SVLS': {}, 'OPERS': {}, 'ABORT': False})
config.update({'VERSION': 'UserBot_IRC-0.4.47'})
filename = "db/config.dat"


def load():
    config.update(cPickle.load(file(filename)))


def save():
    with file(filename, 'w') as conf_file:
        cPickle.dump(config, conf_file)

sn = lambda q: raw_input(q + ' Y/N ?> ').lower() == 'y'


class make:

    def debug(self):
        print 'El modo DEBUG es usado para detectar posibles errores, y asi'
        print 'poder solucionarlos esto debe ser usado solo por developers.'
        config.update({'DEBUG': sn('¿Activar el modo DEBUG?')})

    def prefix(self):
        print 'Prefijo: Establece o actualiza el prefijo usado por el bot,'
        print 'esto es usado para distinguir los comandos del texto plano.'
        config.update({'PRE': raw_input('Prefijo ?> ')})

    def hash(self):
        print 'Encriptacion: Es usado para almacenar contraseñas, solo se '
        print 'soporta los siguientes metodos de encriptado: sha1, sha224,'
        print 'sha256, sha384, sha512, md5.\n'
        print 'Advertencia: Si ya ha definido este parametro anteriormente,'
        print 'cambiarlo puede ser perjudicial para usuarios y operadores,'
        print 'dado que las posibles contraseñas estan almacenadas en las'
        print 'bases de datos con el anterior tipo de encriptado y generar'
        print 'errores de autenticacion.'
        if sn('¿Desea continuar?'):
            config.update({'HASH': raw_input('Hash ?> ')})

    def superuser(self):
        print 'Super Usuarios: Personas con permisos  especiales sobre el bot.'
        print 'Estos pueden eliminar, congelar  usuarios o canales, etc. debe'
        print 'proporcionar una contraseña y un usuario; la contraseña a usar'
        print 'debe estar encriptada en ' + str(config['HASH'])
        if sn('Añadir-/-Actualizar'):
            config['OPERS'].update({raw_input('USER ?> '): raw_input('PASS ?> ')})

        if sn('Eliminar'):
            del config['OPERS'][raw_input('USER ?>')]

    def addserver(self):
        print 'Los servidores a conectar automaticamente por UserBot'
        print 'Los parametros a definir son:'
        print 'Nombre de la red: El nombre del servidor. Ej: Freenode, Hira'
        print 'Servidor: Direccion del servidor. Ej: chat.freenode.net'
        print 'Puerto: El puerto a conectar. Ej: 6667, 6697'
        print 'SSL: Se marca si se usara SSL en la conexion.'
        print 'Nick: El nombre que usara el bot en la red.'
        print 'SASL: Marca el uso de : Simple Authentication and Security Layer'
        print 'Canal Principal: Canal donde el bot muestra los usuarios nuevos'
        print 'registrados, los eliminados, canales nuevos, etc.'
        if sn('¿Desea continuar?'):
            red = raw_input('nombre de la red  ?> ').lower()
            config['SVLS'].update(
                         {red: {'SERV': raw_input('servidor          ?> '),
                                'PORT': int(raw_input('puerto            ?> ')),
                                'NICK': raw_input('nickname          ?> '),
                                'PCHAN': raw_input('canal principal   ?> '),
                                'CHAN': [],
                                'SASL': raw_input('NICKSERV PASS ?> ') if sn('¿Usar SASL?  ') else '',
                                'SSL': sn('¿Activar SSL?')}})

    def delserver(self):
        print 'Se eliminara el servidor en forma total, canales registrados,'
        print 'flags, etc. Servidores disponibles: ' + ', '.join(config['SVLS'])
        if sn('¿Desea continuar?'):
            import channels
            red = raw_input('Nombre de la red ?> ')
            del config['SVLS'][red]
            channels.channels._drop(red)

    def flood(self):
        print 'Cantidad de msg por x intervalo de tiempo que seran enviados'
        print 'NOTA: El tiempo se mide en segundos, usar punto de coma flotante'
        config.update({'FLOOD PROTECTION': float(raw_input('    ?> '))})

    def spt(self):
        print 'Se guardaran las salidas, tanto como las entradas de mensajes en'
        print 'un fichero, esto debe ser habilitado unicamente con intencion de'
        print 'encontrar errores (DEBUG), ya que compromete la confidencialidad'
        print 'del usuario, ya que se guardaran contraseñas, etc.'
        config.update({'SPT': sn('¿Desea guardar el texto plano?')})

    def code(self):
        print 'Codificacion de caracteres a usar, la estandar usada es: utf-8,'
        print 'ya que este es capaz de representar cualquier caracter unicode'
        config.update({'ENCODE': 'utf-8' if sn('¿Usar estandar?') else raw_input('    ?> ')})

    def timeout(self):
        print 'El tiempo donde los usuarios registrados en el bot, seran dados'
        print 'por inactivos, y se le solicitara que se autentiquen una ves,'
        print 'entren de nuevo en actividad.'
        print 'NOTA: El tiempo se mide en segundos, usar punto de coma flotante'
        config.update({'TIMEOUT': float(raw_input('    ?> '))})

    def saveconfig(self):
        print 'Se guardara la configuracion establecida hasta este punto, en un'
        print 'fichero, que es necesario para iniciar el bot.'
        if sn('¿Guardar configuracion?'):
            save()

    def reset(self):
        print 'Se reseteara la configuracion hecha hasta ahora, esto significa,'
        print 'que los servidores, operadores que se añadieran seran borrados.'
        print 'Pero los canales, usuario registrados en las bases de datos, no'
        print 'seran eliminados.'
        if sn('¿Desea continuar?'):
            config.clear()
            config.update(dict.fromkeys(['DEBUG', 'PRE', 'HASH', 'TIMEOUT',
                                         'FLOOD PROTECTION', 'SPT', 'ENCODE']))
            config.update({'SVLS': {}, 'OPERS': {}, 'ABORT': False})

make = make()