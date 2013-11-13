from tornado import ioloop, iostream
import socket
import json
import logging
from collections import OrderedDict
from operator import itemgetter
import time
from pydnode.protocol import Deserializer, Serializer

class DNodeFunctionWrapper(object):

    def __init__(self, path, callback_id=None):
        self.path = path
        self.callback_id = callback_id
        self.created_at = time.time()

    def set_remote(self, remote):
        self.remote = remote

    def __call__(self, *args, **kwargs):
        self.remote.call_remote(self.callback_id, *args)

    def __str__(self):
        return "<DNodeFunctionWrapper callbackid:%s path:%s>" % (self.callback_id, self.path)


class CallBackRegistry(object):
    """
    this is where we store our callbacks.
    """
    def __init__(self, remote=None):
        self.callback_number = 0
        self.remote = remote
        self.map = {}

    def add_callback(self, callback, callback_id=None):
        if not callback_id:
            callback_id = self.callback_number
            self.callback_number += 1
            print "!!! updating callback_number"
        self.map[callback_id] = callback
        print "!!! callbackregistry - ", self.map.keys()
        return callback_id

    def get_callback(self, callback_id):
        print ">>>", self.map
        return self.map[callback_id]

class RemoteCallbackRegistry(CallBackRegistry):

    def add_callback(self, callback, callback_id=None):
        """
        when the function comes from remote they decide the id,
        so we just store it.
        """
        if callback_id:
            self.map[callback_id] = callback
            callback.callback_id = callback_id
        else:
            self.map[callback.callback_id] = callback
        callback.set_remote(self.remote)


class Client(object):

    def __init__(self):
        self.callback_registry = CallBackRegistry()
        self.remote_registry = RemoteCallbackRegistry(remote=self)
        self.callback_registry.add_callback(self.methods, "methods")

    def methods(self, methods):
        print "methods received ", methods
        for k, method in methods.iteritems():
            print "method:::", method
            self.remote_registry.add_callback(method, k)
        self.on_connect()

    def get_args_callbacks_(self, *args):
        print "type of args::: ", type(args)
        serializer = Serializer(list(args), self.callback_registry)
        args = serializer.serialize()
        return args, serializer.callbacks

    def call_remote(self, method, *args):
        parsedargs, callbacks = self.get_args_callbacks_(*args)

        # dnode/nodejs sends us this,
        #   {"method":1,"arguments":["bar","[Function]"],"callbacks":{"3":["1"]},"links":[]}
        # then expects us to call them
        # with this
        #   {"callbacks": {}, "method": 3, "arguments": ["hello XXXX"]}
        # thats why we have this here.
        try:
            method = int(method)
        except:
            pass

        line = json.dumps({
                    'method': method,
                    'arguments': parsedargs,
                    'callbacks': callbacks,
                    'links': []
                }) + "\n"
        self.conn.write(line)

    def __getattr__(self, name):
        try:
            print "self.remote_registry", self.remote_registry.map.keys()
            return self.remote_registry.map[name]
        except:
            raise AttributeError

    def on_connect(self):
        pass

class TcpClient(Client):

    def get_deserializer(self, arguments, callbacks):
        d = Deserializer(arguments=arguments, callbacks=callbacks,
                     wrap_callback_class=DNodeFunctionWrapper,
                     callback_registery=self.remote_registry)
        return d.deserialize()

    def parseline(self, line):
        o = json.loads(line)
        d = self.get_deserializer(o['arguments'], o['callbacks'])
        fn = self.callback_registry.get_callback(o['method'])
        if fn:
            fn(*d)
        self.conn.read_until("\n", self.parseline)

    def connect_callback(self):
        logging.info("%s:%s connected", self.ip, self.port)
        self.conn.read_until(b"\n", self.parseline)

    def connect(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.conn = iostream.IOStream(self.socket)
        self.conn.connect((self.ip, self.port), self.connect_callback)
        ioloop.IOLoop.instance().start()

class WsClient(Client):
    pass


if __name__ == "__main__":

    class MyClient(TcpClient):

        def when_foo_called(self, o, callback):
            print "bar called with", o, callback
            callback("hello XXXX", self.my_callback)

        def callback_in_a_dict(self, o):
            print ">>> callback in a dict", o

        def my_callback(self, o, cb):
            print "!!!!! ------------ !!!!", o, cb
            cb({'callbacks': [self.callback_in_a_dict]})

        def on_connect(self):
            print "connected...."
            self.foo("hello", self.when_foo_called)

    MyClient().connect("localhost", 7071)
