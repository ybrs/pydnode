import json
try:
    from eventlet.green import socket
except Exception as e:
    import socket

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
        print "Sending to server", line
        self.conn.sendall(line)
        self.read_until_newline()

    def read_until_newline(self):
        buffer = ''
        while True:
            line = self.conn.recv(1024)
            buffer += line
            buffer = self.parse_buffer(buffer)
            if not buffer:
                return

    def normalize_callbacks(self, callbacks):
        ret = []
        for k,v in callbacks.iteritems():
            ret.append((k, v))
        return ret

    def replace_functions(self, obj, callbacks):
        if obj == '[Function]':
            functionid, functionpath = callbacks.pop()
            fn = DNodeRemoteFunction(functionid, functionpath, self)
            if functionid not in self.remotecallbacks:
                self.remotecallbacks[functionid] = fn
                return fn
        return obj

    def traverse_result(self, result, callbacks, obj):
        myobj = copyobject(result, self.replace_functions, callbacks)
        return myobj

    def parseline(self, line):
        try:
            o = json.loads(line)
            if isinstance(o['method'], int):
                callbacks = self.normalize_callbacks(o['callbacks'])
                myobj = self.traverse_result(o['arguments'], callbacks, {})
                self.callbacks[o['method']](*myobj)
            else:
                fn = getattr(self.pc, o['method'])
                if fn:
                    fn(o)
        except Exception as e:
            raise

    def parse_buffer(self, buffer):
        c = buffer.index("\n")
        if c:
            self.parseline(buffer[0:c])
            return buffer[c+1:]
        else:
            return buffer

    def connect(self):
        buffer  = ''
        self.conn = socket.socket()
        self.conn.connect((self.ip, self.port))
        print '%s connected' % self.ip
        while True:
            line = self.conn.recv(1024)
            print line
            buffer += line
            buffer = self.parse_buffer(buffer)
            if not buffer:
                return
