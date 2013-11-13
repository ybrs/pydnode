from tornado import ioloop, iostream
import socket
import json
import logging
from collections import OrderedDict
from operator import itemgetter
import time

class DNodeFunctionWrapper(object):

    def __init__(self, path, callback_id=None):
        self.callback_id = callback_id
        self.path = path
        self.created_at = time.time()

    def __call__(self, *args, **kwargs):
        self.client.calldnodemethod(self.callback_id, *args)

    def __str__(self):
        return "<DNodeFunctionWrapper callbackid:%s path:%s>" % (self.callbackid, self.path)


class CallBackRegistry(object):
    """
    this is where we store our callbacks.
    """
    def __init__(self, remote=None):
        self.callback_number = 0
        self.remote = remote
        self.map = {}

    def add_callback(self, callback):
        self.callback_number += 1
        self.map[self.callback_number] = callback
        callback.callback_id = self.callback_number
        return self.callback_number

    def get_callback(self, callback_id):
        return self.map[callback_id]

class RemoteCallbackRegistry(CallBackRegistry):

    def add_callback(self, callback):
        """
        when the function comes from remote they decide the id,
        so we just store it.
        """
        self.map[callback.callback_id] = callback


class ProtocolCommands(object):
    def __init__(self):
       self.rpcmethods = {}

    def methods(self, obj):
        for k, v in obj['arguments'][0].iteritems():
            print k
            self.rpcmethods[k] = True
        print self.rpcmethods

def copyobject(obj, fn, callbacks):
    obj = fn(obj, callbacks)
    if isinstance(obj, dict):
        return {copyobject(key, fn, callbacks): copyobject(value, fn, callbacks) for key, value in obj.items()}
    if hasattr(obj, '__iter__'):
        return type(obj)(copyobject(i, fn, callbacks) for i in obj)
    return obj

class DNodeNode(object):
    """ our base class for dnode server and client
    """

    def normalize_callbacks(self, callbacks):
        """
            we receive callbacks as
                {"callbacks": {"6": [1], "7": [3]},
                    "method": "z2", "arguments": ["foo", "[Function]", "bar", "[Function]"]}
            but in python - and most other languages, dicts are not sorted,
            so we sort them by position.

            so "callbacks": {"6": [1], "7": [3]} might become, {"7": [3], "6": [1]} when we json decode,
            we need to put it in sorted order by their position.
        """
        return sorted(callbacks.iteritems(), key=itemgetter(1))


    def traverse_result(self, result, callbacks, obj):
        myobj = copyobject(result, self.replace_functions, callbacks)
        return myobj

    def prepare_our_args(self, obj, callbacks):
        if callable(obj):
            self.callbacks[self.callbacknumber] = obj
            callbacks[self.callbacknumber] = [self.argcallbackcounter]
            self.callbacknumber += 1
            self.argcallbackcounter += 1
            return '[Function]'
        elif isinstance(obj, str) or isinstance(obj, unicode) or isinstance(obj, int) or isinstance(obj, float):
            self.argcallbackcounter += 1
        elif isinstance(obj, dict) or isinstance(obj, list) or isinstance(obj, tuple):
            pass
        else:
            raise Exception("Cant convert to json, unsupported type: " + str(type(obj)) )
        return obj

    def dnode_method_protocol_line(self, method, *args, **kwargs):
        self.argcallbackcounter = 0
        callbacks = {}
        args = copyobject(args, self.prepare_our_args, callbacks)
        line = json.dumps({
                    'method': method,
                    'arguments': args,
                    'callbacks': callbacks
                }) + "\n"
        print "sending line:", line
        return line

    def replace_functions(self, obj, callbacks):
        if obj == '[Function]':
            functionid, functionpath = callbacks.pop(0)
            fn = DNodeRemoteFunction(functionid, functionpath, self)
            if functionid not in self.remotecallbacks:
                self.remotecallbacks[functionid] = fn
                return fn
        return obj

class DNodeRemote(object):
    """
    this is just a syntatic sugar to call for DNodeClient.calldnodemethod()
    """
    def __init__(self, client):
        self.remote_methods = {}
        self.client = client

    def __getattr__(self, name):
        return self.remote_methods[name]

    def add_method(self, name, path, callbackid):
        self.remote_methods[name] = DNodeRemoteFunction(callbackid, path, self.client)

class DNodeClient(DNodeNode):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.pc = ProtocolCommands()
        self.conn = None
        self.callbacknumber = 1
        self.callbacks = {}
        self.remotecallbacks = {}
        self.remote = DNodeRemote(self)

    def calldnodemethod(self, method, *args, **kwargs):
        line = self.dnode_method_protocol_line(method, *args, **kwargs)
        self.conn.write(line)

    def on_connect(self):
        return

    def parseline(self, line):
        try:
            print "received line", line
            o = json.loads(line)
            if isinstance(o['method'], int):
                callbacks = self.normalize_callbacks(o['callbacks'])
                myobj = self.traverse_result(o['arguments'], callbacks, OrderedDict())
                fn = self.callbacks[o['method']]
                fn(*myobj)
            else:
                if o['method'] == 'methods':
                    for k, v in o['callbacks'].iteritems():
                        self.remote.add_method(str(v[1]), [k], k)
                    self.on_connect()

                fn = getattr(self.pc, o['method'], None)
                if fn:
                    fn(o)
            self.conn.read_until("\n", self.parseline)
        except Exception as e:
            raise

    def connect_callback(self):
        logging.info("%s:%s connected", self.ip, self.port)
        self.conn.read_until(b"\n", self.parseline)

    def close(self):
        self.conn.close()

    def connect(self, on_connect=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.conn = iostream.IOStream(self.socket)
        self.conn.connect((self.ip, self.port), self.connect_callback)
        if on_connect:
            self.on_connect = on_connect
        ioloop.IOLoop.instance().start()
