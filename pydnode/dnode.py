from tornado import ioloop, iostream
import socket
import json
import logging
from collections import OrderedDict

class ProtocolCommands(object):
    def __init__(self):
       self.rpcmethods = {}

    def methods(self, obj):
        for k, v in obj['arguments'][0].iteritems():
            print k
            self.rpcmethods[k] = True
        print self.rpcmethods

class DNodeRemoteFunction(object):

    def __init__(self, callbackid, path, client):
        self.callbackid = callbackid
        self.path = path
        # TODO: this object will never be deleted, because circular ref.
        self.client = client

    def __call__(self, *args, **kwargs):
        self.client.calldnodemethod(int(self.callbackid), *args)

    def __str__(self):
        return "<DNodeRemoteFunction callbackid:%s path:%s>" % (self.callbackid, self.path)

def copyobject(obj, fn, callbacks):
    obj = fn(obj, callbacks)
    if isinstance(obj, dict):
        return {copyobject(key, fn, callbacks): copyobject(value, fn, callbacks) for key, value in obj.items()}
    if hasattr(obj, '__iter__'):
        return type(obj)(copyobject(i, fn, callbacks) for i in obj)
    return obj


class DNodeClient(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.pc = ProtocolCommands()
        self.conn = None
        self.callbacknumber = 1
        self.callbacks = {}
        self.remotecallbacks = {}

    def prepare_our_args(self, obj, callbacks):
        if callable(obj):
            self.callbacks[self.callbacknumber] = obj
            callbacks[self.callbacknumber] = [self.argcallbackcounter]
            self.callbacknumber+=1
            self.argcallbackcounter += 1
            return '[Function]'
        elif isinstance(obj, str) or isinstance(obj, unicode) or isinstance(obj, int) or isinstance(obj, float):
            self.argcallbackcounter += 1
        elif isinstance(obj, dict) or isinstance(obj, list) or isinstance(obj, tuple):
            pass
        else:
            raise Exception("Cant convert to json, unsupported type: " + str(type(obj)) )

        return obj

    def calldnodemethod(self, method, *args, **kwargs):
        self.argcallbackcounter = 0
        callbacks = {}
        args = copyobject(args, self.prepare_our_args, callbacks)
        line = json.dumps({
                    'method': method,
                    'arguments': args,
                    'callbacks': callbacks
                }) + "\n"
        self.conn.write(line)

    def normalize_callbacks(self, callbacks):
        ret = []
        for k,v in callbacks.iteritems():
            ret.append((k, v))
        return ret

    def replace_functions(self, obj, callbacks):
        if obj == '[Function]':
            functionid, functionpath = callbacks.pop(0)
            fn = DNodeRemoteFunction(functionid, functionpath, self)
            if functionid not in self.remotecallbacks:
                self.remotecallbacks[functionid] = fn
                return fn
        return obj

    def traverse_result(self, result, callbacks, obj):
        myobj = copyobject(result, self.replace_functions, callbacks)
        return myobj

    def on_connect(self):
        return

    def parseline(self, line):
        try:
            o = json.loads(line)
            if isinstance(o['method'], int):
                print "received method :::: ", o['method'], "self.callbacks", self.callbacks
                callbacks = self.normalize_callbacks(o['callbacks'])
                myobj = self.traverse_result(o['arguments'], callbacks, OrderedDict)
                fn = self.callbacks[o['method']]
                print ">>>>>", fn, o['method'], myobj
                fn(*myobj)
            else:
                if o['method'] == 'methods':
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
