#
# Copyright 2013, Junta de Andalucia
# http://www.juntadeandalucia.es/
#
# Authors:
#   Alberto Beiztegui <albertobeiz@gmail.com>
#   Pablo Martin <goinnn@gmail.com>
#
# All rights reserved - EUPL License V 1.1
# https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
#

import redis
import simplejson as json

from pyramid.response import Response
from pyramid.threadlocal import get_current_registry

from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.server import SocketIOServer
from socketio.sgunicorn import GeventSocketIOWorker, GunicornWSGIHandler
from socketio.virtsocket import Socket

CHANNEL_WEBSOCKET = 'message'
TOKEN = 'token'


def get_manager():
    settings = get_current_registry().settings
    return redis.Redis.from_url(settings['sockjs_url'])


def is_websockets_enabled():
    settings = get_current_registry().settings
    return settings['server:main:worker_class'] == 'gecoscc.socks.GecosGeventSocketIOWorker'


def invalidate_change(request, objnew):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'token': request.GET.get(TOKEN, ''),
        'action': 'change',
        'objectId': unicode(objnew['_id']),
        'user': request.user['username']
    }))


def invalidate_delete(request, obj):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'token': request.GET.get(TOKEN, ''),
        'action': 'delete',
        'objectId': unicode(obj['_id']),
        'path': obj['path'],
        'user': request.user['username']
    }))


def invalidate_jobs(request, user=None):
    if not is_websockets_enabled():
        return

    user = user or request.user
    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'username': user.get('username'),
        'action': 'jobs',
    }))

def maintenance_mode(_request, msg):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'action': 'maintenance',
        'message': msg
    }))
def update_tree(path = 'root'):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'action': 'update_tree',
        'path': path
    }))


def add_computer_to_user(computer, user):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'action': 'add_computer_to_user',
        'computer': unicode(computer),
        'user': unicode(user)
    }))

def delete_computer(object_id, path):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish(CHANNEL_WEBSOCKET, json.dumps({
        'token': '',
        'action': 'delete',
        'objectId': unicode(object_id),
        'path': path,
        'user': 'Chef server'
    }))

def socktail(logdata):
    if not is_websockets_enabled():
        return

    manager = get_manager()
    manager.publish('logdata', json.dumps({
        'action': 'socktail',
        'logdata': unicode(logdata)
    }))

class GecosWSGIHandler(GunicornWSGIHandler):

    def get_environ(self):
        env = super(GecosWSGIHandler, self).get_environ()
        headers = dict(self._headers())
        if ('HTTP_X_FORWARDED_PROTO' in headers and headers['HTTP_X_FORWARDED_PROTO'] == 'https'):
            env['wsgi.url_scheme'] = 'https'
        return env

class GecosSocketIOServer(SocketIOServer):

    def get_socket(self, sessid=''):
        """Return an existing or new client Socket."""
        socket = self.sockets.get(sessid)

        if socket is None:
            socket = Socket(self, self.config)
            self.sockets[socket.sessid] = socket
        else:
            socket.incr_hits()

        return socket


class GecosGeventSocketIOWorker(GeventSocketIOWorker):

    server_class = GecosSocketIOServer
    wsgi_handler = GecosWSGIHandler
    
    def patch(self):
        # Do not patch the sockets! (compatibility with gunicorn 19.+
        self.sockets_back = self.sockets
        super(GeventSocketIOWorker, self).patch()
        self.sockets = self.sockets_back
    
class TailNamespace(BaseNamespace):
    ''' Defines a namespace for '/tail' endpoint, where socket working for view update log
    '''
    def listener(self):
        if not is_websockets_enabled():
            return

        settings = get_current_registry().settings

        r = redis.StrictRedis.from_url(settings['sockjs_url'])
        r = r.pubsub()

        try:
            r.subscribe('logdata')

            for m in r.listen():
                if m['type'] == 'message':
                    data = json.loads(m['data'])
                    self.emit('logdata', data)
        except redis.ConnectionError:
            self.emit('logdata', {'redis':'error'})

    def on_sendlog(self, *_args, **_kwargs):
        self.spawn(self.listener)

class GecosNamespace(BaseNamespace):

    def listener(self):
        if not is_websockets_enabled():
            return

        settings = get_current_registry().settings

        r = redis.StrictRedis.from_url(settings['sockjs_url'])
        r = r.pubsub()

        try:
            r.subscribe(CHANNEL_WEBSOCKET)

            for m in r.listen():
                if m['type'] == 'message':
                    data = json.loads(m['data'])
                    self.emit(CHANNEL_WEBSOCKET, data)
        except redis.ConnectionError:
            self.emit(CHANNEL_WEBSOCKET, {'redis':'error'})

    def on_subscribe(self, *_args, **_kwargs):
        self.spawn(self.listener)


def socketio_service(request):
    socketio_manage(request.environ, {
        '': GecosNamespace,
        '/tail': TailNamespace
    }, request=request)
    return Response('no-data')
